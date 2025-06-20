from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from datetime import datetime, date
import uvicorn
import os
import logging

# Database imports
from database.connection import (
    get_database, Alumni, Achievement, Project, ImportLog,
    DegreeProgram, AchievementType, ProjectType, check_database_health,
    create_tables  # Add this import
)

# Service imports
from services.csv_service import CSVImportService

# Pydantic models for API
from pydantic import BaseModel
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
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

# Create FastAPI app
app = FastAPI(
    title="AlumDash - Alumni Achievement Tracking System",
    description="Track and monitor achievements of film and television alumni",
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    db_healthy = await check_database_health()
    
    if db_healthy:
        return {"status": "healthy", "database": "connected", "timestamp": datetime.utcnow()}
    else:
        raise HTTPException(status_code=503, detail="Database connection failed")

# Serve HTML interface
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface"""
    try:
        with open("index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Web interface not found")

# Alumni endpoints
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
                degree_program=alumnus.degree_program.value,
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
            degree_program=alumnus.degree_program.value,
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
        try:
            degree_program = DegreeProgram(alumni_data.degree_program)
        except ValueError:
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
            degree_program=degree_program,  # This is already converted to enum
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
            degree_program=new_alumni.degree_program.value,
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

# CSV Import endpoints
@app.post("/api/alumni/import-csv", response_model=ImportResult)
async def import_alumni_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_database)
):
    """Import alumni data from CSV file"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Import using CSV service
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

# Dashboard endpoint
@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(session: AsyncSession = Depends(get_database)):
    """Get dashboard statistics"""
    try:
        # Count totals
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

# Legacy endpoints for compatibility (return empty data since we're using real database now)
@app.get("/api/achievements")
async def get_achievements():
    """Legacy endpoint - achievements now integrated with alumni"""
    return []

@app.get("/api/projects")
async def get_projects():
    """Legacy endpoint - projects functionality to be implemented"""
    return []

@app.get("/api/data-sources")
async def get_data_sources():
    """Legacy endpoint - data sources functionality to be implemented"""
    return []

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AlumDash - Alumni Achievement Tracking System")
    print("="*60)
    print("\nStarting server with PostgreSQL database...")
    print("\n✅ Web Interface: http://localhost:8000")
    print("✅ API Documentation: http://localhost:8000/docs")
    print("✅ Alternative API Docs: http://localhost:8000/redoc")
    print("✅ Health Check: http://localhost:8000/health")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
