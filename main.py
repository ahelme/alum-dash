from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import uvicorn
import os
import logging
import json
import asyncio

# Database imports
from database.connection import (
    get_database, Alumni, Achievement, Project, ImportLog, DataSource, ProjectStreamingPlatform,
    DegreeProgram, AchievementType, ProjectType, DataSourceType, check_database_health,
    create_tables  # Add this import
)

# Service imports
from services.csv_service import CSVImportService

# Pydantic models for API
from pydantic import BaseModel
from typing import Optional
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== EXISTING PYDANTIC MODELS =====
class AlumniCreate(BaseModel):
    name: str
    graduation_year: int
    degree_program: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    imdb_url: Optional[str] = None
    website: Optional[str] = None

class AlumniResponse(BaseModel):
    id: int
    name: str
    graduation_year: int
    degree_program: str
    email: Optional[str]
    linkedin_url: Optional[str]
    imdb_url: Optional[str]
    website: Optional[str]
    created_at: datetime
    updated_at: datetime

class DashboardStats(BaseModel):
    total_alumni: int
    total_achievements: int
    total_projects: int
    recent_achievements: List[Dict[str, Any]]
    achievements_by_year: Dict[int, int]
    top_achievers: List[Dict[str, Any]]

class ImportResult(BaseModel):
    success: bool
    message: str
    statistics: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    import_log_id: int

# ===== NEW AUTOMATION MODELS =====
class AutomationStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class DataSourceStatus(BaseModel):
    name: str
    type: str
    active: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    success_rate: float
    items_found_today: int
    rate_limit: int
    errors: List[str] = []

class AutomationStats(BaseModel):
    discoveries_today: int
    discoveries_change: float
    high_confidence: int
    total_discoveries: int
    active_sources: int
    total_sources: int
    avg_processing_time: float
    status: AutomationStatus
    next_scheduled_run: datetime

class DiscoveryItem(BaseModel):
    id: str
    title: str
    alumni_name: str
    achievement_type: str
    source: str
    confidence: float
    timestamp: datetime
    source_url: Optional[str]
    verified: bool = False

class AutomationToggleRequest(BaseModel):
    action: str  # "start" or "stop"

class ManualRunRequest(BaseModel):
    sources: Optional[List[str]] = None
    alumni_ids: Optional[List[int]] = None

# ===== WEBSOCKET MANAGER =====
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# ===== AUTOMATION STATE =====
automation_state = {
    "status": AutomationStatus.STOPPED,
    "current_progress": [],
    "last_stats_update": datetime.now()
}

# Create FastAPI app
app = FastAPI(
    title="AlumDash - Alumni Achievement Tracking System",
    description="Track and monitor achievements of film and television alumni with automated discovery",
    version="2.0.0"
)

# Startup event to ensure tables exist
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    try:
        await create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for React frontend assets
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

# ===== EXISTING ENDPOINTS =====

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    db_healthy = await check_database_health()
    
    if db_healthy:
        return {"status": "healthy", "database": "connected", "timestamp": datetime.utcnow()}
    else:
        raise HTTPException(status_code=503, detail="Database connection failed")

# Serve React frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend index.html"""
    try:
        with open("static/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend not found - ensure Docker build completed successfully")

# Alumni endpoints (EXISTING - keeping as is)
@app.get("/api/alumni", response_model=List[AlumniResponse])
async def get_alumni(session: AsyncSession = Depends(get_database)):
    """Get all alumni records"""
    try:
        query = select(Alumni).order_by(Alumni.name)
        result = await session.execute(query)
        alumni = result.scalars().all()
        
        return [
            AlumniResponse(
                id=alumnus.id,
                name=alumnus.name,
                graduation_year=alumnus.graduation_year,
                degree_program=alumnus.degree_program,
                email=alumnus.email,
                linkedin_url=alumnus.linkedin_url,
                imdb_url=alumnus.imdb_url,
                website=alumnus.website,
                created_at=alumnus.created_at,
                updated_at=alumnus.updated_at
            )
            for alumnus in alumni
        ]
    except Exception as e:
        logger.error(f"Error fetching alumni: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching alumni data")

@app.get("/api/alumni/{alumni_id}", response_model=AlumniResponse)
async def get_alumni_by_id(alumni_id: int, session: AsyncSession = Depends(get_database)):
    """Get specific alumni by ID"""
    try:
        query = select(Alumni).where(Alumni.id == alumni_id)
        result = await session.execute(query)
        alumnus = result.scalar_one_or_none()
        
        if not alumnus:
            raise HTTPException(status_code=404, detail="Alumni not found")
        
        return AlumniResponse(
            id=alumnus.id,
            name=alumnus.name,
            graduation_year=alumnus.graduation_year,
            degree_program=alumnus.degree_program,
            email=alumnus.email,
            linkedin_url=alumnus.linkedin_url,
            imdb_url=alumnus.imdb_url,
            website=alumnus.website,
            created_at=alumnus.created_at,
            updated_at=alumnus.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alumni {alumni_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching alumni data")

@app.post("/api/alumni", response_model=AlumniResponse)
async def create_alumni(alumni_data: AlumniCreate, session: AsyncSession = Depends(get_database)):
    """Create new alumni record"""
    try:
        # Validate degree program
        valid_programs = ["Film Production", "Screenwriting", "Animation", "Documentary", "Television"]
        if alumni_data.degree_program not in valid_programs:
            raise HTTPException(status_code=400, detail="Invalid degree program")
        
        # Check for duplicate
        existing_query = select(Alumni).where(
            Alumni.name == alumni_data.name,
            Alumni.graduation_year == alumni_data.graduation_year
        )
        existing = await session.execute(existing_query)
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Alumni with this name and graduation year already exists")
        
        # Create new alumni
        new_alumni = Alumni(
            name=alumni_data.name,
            graduation_year=alumni_data.graduation_year,
            degree_program=alumni_data.degree_program,
            email=alumni_data.email,
            linkedin_url=alumni_data.linkedin_url,
            imdb_url=alumni_data.imdb_url,
            website=alumni_data.website
        )
        
        session.add(new_alumni)
        await session.commit()
        await session.refresh(new_alumni)
        
        return AlumniResponse(
            id=new_alumni.id,
            name=new_alumni.name,
            graduation_year=new_alumni.graduation_year,
            degree_program=new_alumni.degree_program,
            email=new_alumni.email,
            linkedin_url=new_alumni.linkedin_url,
            imdb_url=new_alumni.imdb_url,
            website=new_alumni.website,
            created_at=new_alumni.created_at,
            updated_at=new_alumni.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alumni: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating alumni record")

# CSV Import endpoints (EXISTING)
@app.post("/api/alumni/import-csv", response_model=ImportResult)
async def import_alumni_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_database)
):
    """Import alumni data from CSV file"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        result = await CSVImportService.import_alumni_csv(
            session=session,
            csv_content=csv_content,
            filename=file.filename,
            imported_by="web_upload"
        )
        
        return ImportResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

@app.get("/api/alumni/csv-template")
async def download_csv_template():
    """Download CSV template for alumni import"""
    try:
        template_csv = CSVImportService.generate_csv_template()
        
        return Response(
            content=template_csv,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=alumni_import_template.csv"}
        )
    except Exception as e:
        logger.error(f"Error generating CSV template: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating CSV template")

@app.get("/api/import-history")
async def get_import_history(session: AsyncSession = Depends(get_database)):
    """Get history of CSV imports"""
    try:
        return await CSVImportService.get_import_history(session)
    except Exception as e:
        logger.error(f"Error fetching import history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching import history")

# Dashboard endpoint (EXISTING)
@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(session: AsyncSession = Depends(get_database)):
    """Get dashboard statistics"""
    try:
        alumni_count_query = select(func.count(Alumni.id))
        alumni_count = await session.execute(alumni_count_query)
        total_alumni = alumni_count.scalar()
        
        achievements_count_query = select(func.count(Achievement.id))
        achievements_count = await session.execute(achievements_count_query)
        total_achievements = achievements_count.scalar()
        
        projects_count_query = select(func.count(Project.id))
        projects_count = await session.execute(projects_count_query)
        total_projects = projects_count.scalar()
        
        # Get recent achievements
        recent_achievements_query = (
            select(Achievement, Alumni.name)
            .join(Alumni, Achievement.alumni_id == Alumni.id)
            .order_by(Achievement.date.desc())
            .limit(5)
        )
        recent_result = await session.execute(recent_achievements_query)
        recent_achievements = [
            {
                "title": achievement.title,
                "alumni_name": alumni_name,
                "date": achievement.date.isoformat(),
                "type": achievement.type.value
            }
            for achievement, alumni_name in recent_result.all()
        ]
        
        # Get achievements by year
        achievements_by_year_query = (
            select(func.extract('year', Achievement.date), func.count(Achievement.id))
            .group_by(func.extract('year', Achievement.date))
            .order_by(func.extract('year', Achievement.date))
        )
        year_result = await session.execute(achievements_by_year_query)
        achievements_by_year = {int(year): count for year, count in year_result.all()}
        
        # Get top achievers
        top_achievers_query = (
            select(Alumni.name, Alumni.graduation_year, func.count(Achievement.id).label('achievement_count'))
            .join(Achievement, Alumni.id == Achievement.alumni_id)
            .group_by(Alumni.id, Alumni.name, Alumni.graduation_year)
            .order_by(func.count(Achievement.id).desc())
            .limit(5)
        )
        top_result = await session.execute(top_achievers_query)
        top_achievers = [
            {
                "name": name,
                "graduation_year": graduation_year,
                "achievement_count": achievement_count
            }
            for name, graduation_year, achievement_count in top_result.all()
        ]
        
        return DashboardStats(
            total_alumni=total_alumni,
            total_achievements=total_achievements,
            total_projects=total_projects,
            recent_achievements=recent_achievements,
            achievements_by_year=achievements_by_year,
            top_achievers=top_achievers
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching dashboard statistics")

# ===== NEW AUTOMATION ENDPOINTS =====

@app.websocket("/ws/automation")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time automation updates"""
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "status": automation_state["status"]
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/automation/status", response_model=AutomationStats)
async def get_automation_status(session: AsyncSession = Depends(get_database)):
    """Get current automation status and statistics"""
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Mock data for now - replace with real queries when achievements table has automation data
        return AutomationStats(
            discoveries_today=24,
            discoveries_change=18.5,
            high_confidence=19,
            total_discoveries=24,
            active_sources=8,
            total_sources=10,
            avg_processing_time=12.5,
            status=automation_state["status"],
            next_scheduled_run=datetime.now() + timedelta(hours=2)
        )
            
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving automation status")

@app.get("/api/automation/sources", response_model=List[DataSourceStatus])
async def get_data_sources():
    """Get status of all data sources"""
    try:
        # Mock data for now - replace with real monitoring when implemented
        sources = [
            DataSourceStatus(
                name="TMDb",
                type="API",
                active=True,
                last_run=datetime.now() - timedelta(hours=2),
                next_run=datetime.now() + timedelta(hours=4),
                success_rate=95.0,
                items_found_today=12,
                rate_limit=40,
                errors=[]
            ),
            DataSourceStatus(
                name="Variety",
                type="Web Scraping",
                active=True,
                last_run=datetime.now() - timedelta(hours=1),
                next_run=datetime.now() + timedelta(hours=5),
                success_rate=76.0,
                items_found_today=4,
                rate_limit=10,
                errors=["Rate limit reached at 14:30"]
            ),
        ]
        
        return sources
        
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving data sources")

@app.get("/api/automation/discoveries", response_model=List[DiscoveryItem])
async def get_recent_discoveries(limit: int = 50, verified_only: bool = False):
    """Get recent discoveries from automation"""
    try:
        # Mock data for now - replace with real achievements when automation is active
        discoveries = [
            DiscoveryItem(
                id="1",
                title="AACTA Award - Best Short Film",
                alumni_name="Sarah Chen",
                achievement_type="Award",
                source="AACTA",
                confidence=0.95,
                timestamp=datetime.now() - timedelta(minutes=2),
                source_url="https://aacta.org/winners",
                verified=False
            ),
            DiscoveryItem(
                id="2",
                title="Producer - Night Terrors",
                alumni_name="James Mitchell",
                achievement_type="Production Credit",
                source="TMDb",
                confidence=0.87,
                timestamp=datetime.now() - timedelta(minutes=15),
                source_url="https://themoviedb.org",
                verified=False
            ),
        ]
        
        return discoveries[:limit]
            
    except Exception as e:
        logger.error(f"Error getting discoveries: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving discoveries")

@app.post("/api/automation/toggle")
async def toggle_automation(request: AutomationToggleRequest, background_tasks: BackgroundTasks):
    """Start or stop the automation system"""
    try:
        if request.action == "start":
            automation_state["status"] = AutomationStatus.RUNNING
            
            await manager.broadcast({
                "type": "status_change",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
            return {"message": "Automation started successfully", "status": "running"}
            
        elif request.action == "stop":
            automation_state["status"] = AutomationStatus.STOPPED
            
            await manager.broadcast({
                "type": "status_change", 
                "status": "stopped",
                "timestamp": datetime.now().isoformat()
            })
            
            return {"message": "Automation stopped successfully", "status": "stopped"}
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")
            
    except Exception as e:
        logger.error(f"Error toggling automation: {e}")
        automation_state["status"] = AutomationStatus.ERROR
        raise HTTPException(status_code=500, detail="Error toggling automation")

@app.post("/api/automation/manual-run")
async def manual_run(request: ManualRunRequest, background_tasks: BackgroundTasks):
    """Trigger a manual collection run"""
    try:
        await manager.broadcast({
            "type": "manual_run_started",
            "sources": request.sources,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": "Manual collection started", "status": "initiated"}
        
    except Exception as e:
        logger.error(f"Error starting manual run: {e}")
        raise HTTPException(status_code=500, detail="Error starting manual collection")

# Legacy endpoints for compatibility
@app.get("/api/achievements")
async def get_achievements():
    """Legacy endpoint - achievements now integrated with alumni"""
    return []

@app.get("/api/projects")
async def get_projects():
    """Legacy endpoint - projects functionality to be implemented"""
    return []

@app.get("/api/data-sources")
async def get_data_sources_legacy():
    """Legacy endpoint - use /api/automation/sources instead"""
    return []

# Catch-all route for React Router (must be last)
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_react_app(full_path: str):
    """
    Catch-all route to serve React app for client-side routing.
    This handles all routes not matched by API endpoints above.
    """
    try:
        with open("static/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend not found - ensure Docker build completed successfully")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AlumDash - Alumni Achievement Tracking System")
    print("="*60)
    print("\nStarting server with PostgreSQL database and automation...")
    print("\n✅ Web Interface: http://localhost:8000")
    print("✅ API Documentation: http://localhost:8000/docs")
    print("✅ Alternative API Docs: http://localhost:8000/redoc")
    print("✅ Health Check: http://localhost:8000/health")
    print("✅ Automation WebSocket: ws://localhost:8000/ws/automation")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
