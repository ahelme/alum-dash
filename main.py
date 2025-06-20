from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any
from datetime import datetime, date
import uvicorn

from models import (
    Alumni, Achievement, Project, AlumniProject, 
    DashboardStats, DataSource, DegreeProgram, AchievementType
)
from database import (
    mock_alumni, mock_achievements, mock_projects,
    get_alumni_by_id, create_alumni_record,
    get_achievements_by_alumni, create_achievement_record
)

# Create FastAPI app
app = FastAPI(
    title="VCA Alumni Achievement Tracking System",
    description="Track and monitor achievements of VCA Film and Television alumni",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve HTML
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r") as f:
        return f.read()

# API Endpoints
@app.get("/api/alumni", response_model=List[Alumni])
async def get_alumni():
    """Get all alumni records"""
    return mock_alumni

@app.get("/api/alumni/{alumni_id}", response_model=Alumni)
async def get_alumni_endpoint(alumni_id: int):
    """Get specific alumni by ID"""
    alumni = get_alumni_by_id(alumni_id)
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")
    return alumni

@app.post("/api/alumni", response_model=Alumni)
async def create_alumni(alumni: Alumni):
    """Create new alumni record"""
    return create_alumni_record(alumni)

@app.get("/api/achievements", response_model=List[Achievement])
async def get_achievements():
    """Get all achievements"""
    return mock_achievements

@app.get("/api/achievements/alumni/{alumni_id}", response_model=List[Achievement])
async def get_alumni_achievements(alumni_id: int):
    """Get achievements for specific alumni"""
    return get_achievements_by_alumni(alumni_id)

@app.post("/api/achievements", response_model=Achievement)
async def create_achievement(achievement: Achievement):
    """Create new achievement record"""
    return create_achievement_record(achievement)

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    # Calculate achievements by year
    achievements_by_year = {}
    for achievement in mock_achievements:
        year = achievement.date.year
        achievements_by_year[year] = achievements_by_year.get(year, 0) + 1
    
    # Calculate top achievers
    top_achievers = []
    for alumni in mock_alumni:
        achievement_count = len([a for a in mock_achievements if a.alumni_id == alumni.id])
        if achievement_count > 0:
            top_achievers.append({
                "name": alumni.name,
                "graduation_year": alumni.graduation_year,
                "achievement_count": achievement_count
            })
    
    top_achievers.sort(key=lambda x: x["achievement_count"], reverse=True)
    
    # Get recent achievements
    recent_achievements = []
    for a in sorted(mock_achievements, key=lambda x: x.date, reverse=True)[:5]:
        alumni = get_alumni_by_id(a.alumni_id)
        recent_achievements.append({
            "title": a.title,
            "alumni_name": alumni.name if alumni else "Unknown",
            "date": a.date.isoformat(),
            "type": a.type.value
        })
    
    return DashboardStats(
        total_alumni=len(mock_alumni),
        total_achievements=len(mock_achievements),
        recent_achievements=recent_achievements,
        achievements_by_year=achievements_by_year,
        top_achievers=top_achievers[:5]
    )

@app.get("/api/data-sources", response_model=List[DataSource])
async def get_data_sources():
    """Get configured data sources"""
    return [
        DataSource(
            name="TMDb API",
            type="API",
            url="https://api.themoviedb.org/3",
            active=True,
            rate_limit=40,
            last_checked=datetime.now()
        ),
        DataSource(
            name="OMDb API",
            type="API",
            url="http://www.omdbapi.com",
            active=True,
            rate_limit=1000,
            last_checked=datetime.now()
        ),
        DataSource(
            name="Screen Australia",
            type="RSS",
            url="https://www.screenaustralia.gov.au/rss",
            active=True,
            rate_limit=10
        ),
        DataSource(
            name="IF Magazine",
            type="Web Scraping",
            url="https://if.com.au",
            active=True,
            rate_limit=6
        ),
        DataSource(
            name="AACTA Awards",
            type="Web Scraping",
            url="https://www.aacta.org",
            active=False,
            rate_limit=5
        )
    ]

@app.get("/api/projects", response_model=List[Project])
async def get_projects():
    """Get all projects"""
    return mock_projects

if __name__ == "__main__":
    print("\n" + "="*60)
    print("VCA Alumni Achievement Tracking System")
    print("="*60)
    print("\nStarting server...")
    print("\n✅ Web Interface: http://localhost:8000")
    print("✅ API Documentation: http://localhost:8000/docs")
    print("✅ Alternative API Docs: http://localhost:8000/redoc")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)