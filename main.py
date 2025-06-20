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
    get_database, Alumni, Achievement, Project, ImportLog, DataSource, ProjectStreamingPlatform, AutomationState,
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

# ===== DISCOVERY PIPELINE FRAMEWORK =====

class DiscoveryPipeline:
    """Core discovery pipeline for processing data sources and finding achievements"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.discoveries = []
        self.processed_sources = 0
        self.total_sources = 0
        
    async def run_discovery(self) -> Dict[str, Any]:
        """Main discovery pipeline execution"""
        try:
            # Get active data sources
            sources = await self._get_active_sources()
            self.total_sources = len(sources)
            
            logger.info(f"Starting discovery pipeline with {self.total_sources} active sources")
            
            # Process each source
            for source in sources:
                try:
                    discoveries = await self._process_data_source(source)
                    for discovery in discoveries:
                        confidence = await self._calculate_confidence_score(discovery, source)
                        await self._save_discovery(discovery, confidence, source)
                        self.discoveries.append(discovery)
                    
                    self.processed_sources += 1
                    await self._update_source_stats(source, success=True)
                    
                except Exception as e:
                    logger.error(f"Error processing source {source.name}: {e}")
                    await self._update_source_stats(source, success=False, error=str(e))
            
            result = {
                "total_sources": self.total_sources,
                "processed_sources": self.processed_sources,
                "discoveries_found": len(self.discoveries),
                "discoveries": self.discoveries
            }
            
            logger.info(f"Discovery pipeline completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Discovery pipeline failed: {e}")
            raise
    
    async def _get_active_sources(self) -> List[DataSource]:
        """Get all active data sources from database"""
        query = select(DataSource).where(DataSource.active == True).order_by(DataSource.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def _process_data_source(self, source: DataSource) -> List[Dict[str, Any]]:
        """Process individual data source based on type"""
        discoveries = []
        
        try:
            if source.type == DataSourceType.API:
                discoveries = await self._process_api_source(source)
            elif source.type == DataSourceType.RSS:
                discoveries = await self._process_rss_source(source)
            elif source.type == DataSourceType.WEB_SCRAPING:
                discoveries = await self._process_web_scraping_source(source)
            
            logger.info(f"Source {source.name} yielded {len(discoveries)} potential discoveries")
            
        except Exception as e:
            logger.error(f"Failed to process {source.name}: {e}")
            
        return discoveries
    
    async def _process_api_source(self, source: DataSource) -> List[Dict[str, Any]]:
        """Process API-based data sources (TMDb, OMDb, etc.)"""
        discoveries = []
        
        # Get alumni to search for
        alumni_query = select(Alumni).limit(10)  # Limit for development
        alumni_result = await self.session.execute(alumni_query)
        alumni = alumni_result.scalars().all()
        
        for alumnus in alumni:
            # Simulate API discovery for each alumnus
            if source.name == "TMDb API":
                discovery = {
                    "title": f"Producer Credit - New Film Project",
                    "alumni_id": alumnus.id,
                    "alumni_name": alumnus.name,
                    "achievement_type": "Production Credit",
                    "description": f"Found {alumnus.name} credited as producer on new film project",
                    "date": datetime.now().date(),
                    "source_url": f"https://themoviedb.org/person/{alumnus.id}",
                    "raw_data": {"source": "TMDb", "confidence_factors": ["name_match", "graduation_year"]}
                }
                discoveries.append(discovery)
                
            elif source.name == "OMDb API":
                discovery = {
                    "title": f"Director - Independent Film",
                    "alumni_id": alumnus.id,
                    "alumni_name": alumnus.name,
                    "achievement_type": "Production Credit", 
                    "description": f"Found {alumnus.name} listed as director on independent film",
                    "date": datetime.now().date(),
                    "source_url": f"https://imdb.com/name/{alumnus.id}",
                    "raw_data": {"source": "OMDb", "confidence_factors": ["exact_name_match"]}
                }
                discoveries.append(discovery)
        
        return discoveries[:3]  # Limit discoveries for development
    
    async def _process_rss_source(self, source: DataSource) -> List[Dict[str, Any]]:
        """Process RSS feed sources (news, industry publications)"""
        discoveries = []
        
        # Simulate RSS feed processing
        if source.name == "Screen Australia":
            discovery = {
                "title": "Funding Grant Recipient",
                "alumni_id": 1,  # Sarah Chen
                "alumni_name": "Sarah Chen",
                "achievement_type": "Industry Recognition",
                "description": "Received Screen Australia development funding for new project",
                "date": datetime.now().date(),
                "source_url": "https://screenaustralia.gov.au/funding-recipients",
                "raw_data": {"source": "Screen Australia", "confidence_factors": ["official_announcement"]}
            }
            discoveries.append(discovery)
        
        return discoveries
    
    async def _process_web_scraping_source(self, source: DataSource) -> List[Dict[str, Any]]:
        """Process web scraping sources (festival sites, award sites)"""
        discoveries = []
        
        # Simulate web scraping
        if source.name == "IF Magazine":
            discovery = {
                "title": "Featured in Industry Interview",
                "alumni_id": 2,  # James Mitchell
                "alumni_name": "James Mitchell", 
                "achievement_type": "Industry Recognition",
                "description": "Featured in IF Magazine interview about documentary filmmaking",
                "date": datetime.now().date(),
                "source_url": "https://if.com.au/interviews",
                "raw_data": {"source": "IF Magazine", "confidence_factors": ["byline_match", "bio_details"]}
            }
            discoveries.append(discovery)
            
        elif source.name == "AACTA Awards":
            discovery = {
                "title": "AACTA Award Nomination",
                "alumni_id": 3,  # Emma Rodriguez
                "alumni_name": "Emma Rodriguez",
                "achievement_type": "Award",
                "description": "Nominated for AACTA Award for Best Animation",
                "date": datetime.now().date(),
                "source_url": "https://aacta.org/nominations",
                "raw_data": {"source": "AACTA", "confidence_factors": ["official_nomination_list"]}
            }
            discoveries.append(discovery)
        
        return discoveries
    
    async def _calculate_confidence_score(self, discovery: Dict[str, Any], source: DataSource) -> float:
        """Calculate confidence score for a discovery"""
        base_confidence = 0.5
        confidence_factors = discovery.get("raw_data", {}).get("confidence_factors", [])
        
        # Source reliability bonus
        source_bonuses = {
            "TMDb API": 0.2,
            "OMDb API": 0.25,
            "Screen Australia": 0.3,  # Official government source
            "AACTA Awards": 0.35,     # Official awards body
            "IF Magazine": 0.15       # Industry publication
        }
        base_confidence += source_bonuses.get(source.name, 0.1)
        
        # Confidence factor bonuses
        factor_bonuses = {
            "exact_name_match": 0.2,
            "name_match": 0.15,
            "graduation_year": 0.1,
            "official_announcement": 0.25,
            "byline_match": 0.15,
            "bio_details": 0.1,
            "official_nomination_list": 0.3
        }
        
        for factor in confidence_factors:
            base_confidence += factor_bonuses.get(factor, 0.05)
        
        # Achievement type reliability
        type_multipliers = {
            "Award": 1.1,
            "Industry Recognition": 1.05,
            "Production Credit": 1.0,
            "Festival Selection": 1.0,
            "Review/Reception": 0.9
        }
        
        achievement_type = discovery.get("achievement_type", "Production Credit")
        base_confidence *= type_multipliers.get(achievement_type, 1.0)
        
        # Cap confidence at 1.0
        return min(base_confidence, 1.0)
    
    async def _save_discovery(self, discovery: Dict[str, Any], confidence: float, source: DataSource):
        """Save discovery as achievement if confidence threshold met"""
        
        # Only save discoveries with confidence > 0.7
        if confidence < 0.7:
            logger.info(f"Skipping low confidence discovery: {discovery['title']} (confidence: {confidence:.2f})")
            return
        
        # Check for duplicates
        existing_query = select(Achievement).where(
            Achievement.alumni_id == discovery["alumni_id"],
            Achievement.title == discovery["title"],
            Achievement.source == source.name
        )
        existing_result = await self.session.execute(existing_query)
        if existing_result.scalar_one_or_none():
            logger.info(f"Duplicate discovery skipped: {discovery['title']}")
            return
        
        # Create new achievement
        try:
            achievement = Achievement(
                alumni_id=discovery["alumni_id"],
                type=AchievementType(discovery["achievement_type"]),
                title=discovery["title"],
                date=discovery["date"],
                description=discovery["description"],
                confidence_score=confidence,
                verified=False,  # All discoveries start unverified
                source=source.name,
                source_url=discovery.get("source_url")
            )
            
            self.session.add(achievement)
            await self.session.commit()
            
            logger.info(f"Saved new achievement: {discovery['title']} (confidence: {confidence:.2f})")
            
            # Broadcast new discovery via WebSocket
            await manager.broadcast({
                "type": "new_discovery",
                "discovery": {
                    "id": str(achievement.id),
                    "title": achievement.title,
                    "alumni_name": discovery["alumni_name"],
                    "achievement_type": achievement.type.value,
                    "source": source.name,
                    "confidence": float(confidence),
                    "timestamp": datetime.now().isoformat(),
                    "source_url": discovery.get("source_url"),
                    "verified": False
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to save discovery: {e}")
            await self.session.rollback()
    
    async def _update_source_stats(self, source: DataSource, success: bool, error: str = None):
        """Update data source statistics after processing"""
        try:
            source.last_checked = datetime.now()
            
            if success:
                # Improve success rate
                current_rate = source.success_rate or 0.8
                source.success_rate = min(current_rate + 0.1, 1.0)
                source.last_error = None
            else:
                # Decrease success rate
                current_rate = source.success_rate or 0.8
                source.success_rate = max(current_rate - 0.2, 0.1)
                source.last_error = error
            
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update source stats for {source.name}: {e}")

# ===== AUTOMATION STATE MANAGEMENT =====
async def get_automation_state(session: AsyncSession) -> AutomationState:
    """Get current automation state from database, create if not exists"""
    query = select(AutomationState).order_by(AutomationState.id.desc()).limit(1)
    result = await session.execute(query)
    state = result.scalar_one_or_none()
    
    if not state:
        # Create initial state
        state = AutomationState(
            status="stopped",
            next_scheduled_run=datetime.now() + timedelta(hours=6),
            current_progress={},
            run_count=0
        )
        session.add(state)
        await session.commit()
        await session.refresh(state)
    
    return state

async def update_automation_state(session: AsyncSession, **kwargs) -> AutomationState:
    """Update automation state in database"""
    state = await get_automation_state(session)
    
    for key, value in kwargs.items():
        if hasattr(state, key):
            setattr(state, key, value)
    
    await session.commit()
    await session.refresh(state)
    return state

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
        # Send initial status
        async with AsyncSessionLocal() as session:
            db_state = await get_automation_state(session)
            await websocket.send_text(json.dumps({
                "type": "status_update",
                "status": db_state.status,
                "timestamp": datetime.now().isoformat(),
                "next_scheduled_run": db_state.next_scheduled_run.isoformat() if db_state.next_scheduled_run else None,
                "run_count": db_state.run_count
            }))
        
        while True:
            await asyncio.sleep(10)  # Reduced frequency for heartbeat
            
            # Send periodic status update with real data
            async with AsyncSessionLocal() as session:
                db_state = await get_automation_state(session)
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "status": db_state.status,
                    "last_run_start": db_state.last_run_start.isoformat() if db_state.last_run_start else None,
                    "last_run_end": db_state.last_run_end.isoformat() if db_state.last_run_end else None
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/automation/status", response_model=AutomationStats)
async def get_automation_status(session: AsyncSession = Depends(get_database)):
    """Get current automation status and statistics from database"""
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Query real data source statistics
        sources_query = select(DataSource)
        sources_result = await session.execute(sources_query)
        all_sources = sources_result.scalars().all()
        
        active_sources = sum(1 for source in all_sources if source.active)
        total_sources = len(all_sources)
        
        # Query achievements for discovery statistics
        # Discoveries today - achievements created today with automation sources
        discoveries_today_query = select(func.count(Achievement.id)).where(
            Achievement.created_at >= today_start,
            Achievement.source.in_(['TMDb API', 'OMDb API', 'Screen Australia', 'IF Magazine', 'AACTA Awards'])
        )
        discoveries_today_result = await session.execute(discoveries_today_query)
        discoveries_today = discoveries_today_result.scalar() or 0
        
        # High confidence discoveries (confidence > 0.8)
        high_confidence_query = select(func.count(Achievement.id)).where(
            Achievement.created_at >= today_start,
            Achievement.confidence_score > 0.8,
            Achievement.source.in_(['TMDb API', 'OMDb API', 'Screen Australia', 'IF Magazine', 'AACTA Awards'])
        )
        high_confidence_result = await session.execute(high_confidence_query)
        high_confidence = high_confidence_result.scalar() or 0
        
        # Total discoveries (all time automation)
        total_discoveries_query = select(func.count(Achievement.id)).where(
            Achievement.source.in_(['TMDb API', 'OMDb API', 'Screen Australia', 'IF Magazine', 'AACTA Awards'])
        )
        total_discoveries_result = await session.execute(total_discoveries_query)
        total_discoveries = total_discoveries_result.scalar() or 0
        
        # Calculate discoveries change (compare with yesterday)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_query = select(func.count(Achievement.id)).where(
            Achievement.created_at >= yesterday_start,
            Achievement.created_at < today_start,
            Achievement.source.in_(['TMDb API', 'OMDb API', 'Screen Australia', 'IF Magazine', 'AACTA Awards'])
        )
        yesterday_result = await session.execute(yesterday_query)
        yesterday_count = yesterday_result.scalar() or 0
        
        discoveries_change = 0.0
        if yesterday_count > 0:
            discoveries_change = ((discoveries_today - yesterday_count) / yesterday_count) * 100
        elif discoveries_today > 0:
            discoveries_change = 100.0  # 100% increase from 0
        
        # Calculate average processing time from active sources
        avg_processing_time = 15.0  # Default estimate
        active_source_count = sum(1 for source in all_sources if source.active and source.last_checked)
        if active_source_count > 0:
            # Estimate based on source types and success rates
            total_time = 0
            for source in all_sources:
                if source.active and source.success_rate:
                    # Estimate processing time based on source type
                    base_times = {"API": 5, "RSS": 8, "Web Scraping": 20}
                    base_time = base_times.get(source.type.value, 10)
                    # Adjust for success rate (lower success = more time due to retries)
                    adjusted_time = base_time / max(source.success_rate, 0.1)
                    total_time += adjusted_time
            avg_processing_time = total_time / active_source_count if active_source_count > 0 else 15.0
        
        # Get automation state from database
        db_state = await get_automation_state(session)
        
        return AutomationStats(
            discoveries_today=discoveries_today,
            discoveries_change=round(discoveries_change, 1),
            high_confidence=high_confidence,
            total_discoveries=total_discoveries,
            active_sources=active_sources,
            total_sources=total_sources,
            avg_processing_time=round(avg_processing_time, 1),
            status=AutomationStatus(db_state.status),
            next_scheduled_run=db_state.next_scheduled_run or (datetime.now() + timedelta(hours=6))
        )
            
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving automation status")

@app.get("/api/automation/sources", response_model=List[DataSourceStatus])
async def get_data_sources(session: AsyncSession = Depends(get_database)):
    """Get status of all data sources from database"""
    try:
        # Query real data sources from database
        query = select(DataSource).order_by(DataSource.name)
        result = await session.execute(query)
        data_sources = result.scalars().all()
        
        # Convert database models to API response models
        source_statuses = []
        for source in data_sources:
            # Calculate next_run based on last_checked and typical intervals
            next_run = None
            if source.last_checked:
                # Default 6-hour interval for automation runs
                next_run = source.last_checked + timedelta(hours=6)
            
            # Parse errors from last_error field
            errors = []
            if source.last_error:
                errors = [source.last_error]
            
            # Calculate items found today (mock for now - will be real in Phase 2)
            items_found_today = 0
            if source.active and source.success_rate > 0.5:
                # Estimate based on source type and success rate
                base_items = {"API": 10, "RSS": 5, "Web Scraping": 3}
                items_found_today = int(base_items.get(source.type.value, 2) * source.success_rate)
            
            source_status = DataSourceStatus(
                name=source.name,
                type=source.type.value,
                active=source.active,
                last_run=source.last_checked,
                next_run=next_run,
                success_rate=float(source.success_rate * 100) if source.success_rate else 0.0,
                items_found_today=items_found_today,
                rate_limit=source.rate_limit,
                errors=errors
            )
            source_statuses.append(source_status)
        
        return source_statuses
        
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving data sources")

@app.get("/api/automation/discoveries", response_model=List[DiscoveryItem])
async def get_recent_discoveries(limit: int = 50, verified_only: bool = False, session: AsyncSession = Depends(get_database)):
    """Get recent discoveries from automation"""
    try:
        # Query real achievements from automation sources
        automation_sources = ['TMDb API', 'OMDb API', 'Screen Australia', 'IF Magazine', 'AACTA Awards']
        
        query = select(Achievement, Alumni.name).join(
            Alumni, Achievement.alumni_id == Alumni.id
        ).where(
            Achievement.source.in_(automation_sources)
        ).order_by(Achievement.created_at.desc()).limit(limit)
        
        if verified_only:
            query = query.where(Achievement.verified == True)
        
        result = await session.execute(query)
        achievement_data = result.all()
        
        discoveries = []
        for achievement, alumni_name in achievement_data:
            try:
                # Handle achievement type conversion safely
                if hasattr(achievement.type, 'value'):
                    achievement_type_value = achievement.type.value
                else:
                    achievement_type_value = str(achievement.type)
                
                discovery = DiscoveryItem(
                    id=str(achievement.id),
                    title=achievement.title,
                    alumni_name=alumni_name,
                    achievement_type=achievement_type_value,
                    source=achievement.source,
                    confidence=float(achievement.confidence_score),
                    timestamp=achievement.created_at.isoformat(),
                    source_url=achievement.source_url,
                    verified=achievement.verified
                )
                discoveries.append(discovery)
            except Exception as e:
                logger.error(f"Error processing achievement {achievement.id}: {e}")
                # Skip this achievement and continue
        
        return discoveries
            
    except Exception as e:
        logger.error(f"Error getting discoveries: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving discoveries")

# Background task function for automation discovery
async def run_automation_background_task():
    """Background task that runs the discovery pipeline"""
    try:
        async with AsyncSessionLocal() as session:
            # Update status to running
            await update_automation_state(session, status="running", last_run_start=datetime.now())
            
            # Broadcast start notification
            await manager.broadcast({
                "type": "automation_started",
                "timestamp": datetime.now().isoformat(),
                "message": "Discovery pipeline started"
            })
            
            # Run discovery pipeline
            pipeline = DiscoveryPipeline(session)
            result = await pipeline.run_discovery()
            
            # Update automation state with results
            await update_automation_state(
                session,
                status="stopped",
                last_run_end=datetime.now(),
                next_scheduled_run=datetime.now() + timedelta(hours=6),
                run_count=result.get("processed_sources", 0)
            )
            
            # Broadcast completion
            await manager.broadcast({
                "type": "automation_completed",
                "timestamp": datetime.now().isoformat(),
                "result": {
                    "discoveries_found": result.get("discoveries_found", 0),
                    "sources_processed": result.get("processed_sources", 0),
                    "total_sources": result.get("total_sources", 0)
                }
            })
            
            logger.info(f"Automation run completed: {result}")
            
    except Exception as e:
        logger.error(f"Automation background task failed: {e}")
        
        # Update status to error
        async with AsyncSessionLocal() as session:
            await update_automation_state(
                session,
                status="error",
                last_run_end=datetime.now()
            )
        
        # Broadcast error
        await manager.broadcast({
            "type": "automation_error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        })

@app.post("/api/automation/toggle")
async def toggle_automation(request: AutomationToggleRequest, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_database)):
    """Start or stop the automation system"""
    try:
        if request.action == "start":
            # Update database state
            await update_automation_state(
                session, 
                status="running",
                last_run_start=datetime.now(),
                next_scheduled_run=datetime.now() + timedelta(hours=6)
            )
            
            # Start background automation task
            background_tasks.add_task(run_automation_background_task)
            
            # Update in-memory state for compatibility
            automation_state["status"] = AutomationStatus.RUNNING
            
            await manager.broadcast({
                "type": "status_change",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
            return {"message": "Automation started successfully", "status": "running"}
            
        elif request.action == "stop":
            # Update database state
            await update_automation_state(
                session,
                status="stopped", 
                last_run_end=datetime.now()
            )
            
            # Update in-memory state for compatibility
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
        # Add background task for manual discovery run
        background_tasks.add_task(run_automation_background_task)
        
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
