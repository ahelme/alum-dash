from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class DegreeProgram(str, Enum):
    """Enumeration of available degree programs"""
    FILM_PRODUCTION = "Film Production"
    SCREENWRITING = "Screenwriting"
    ANIMATION = "Animation"
    DOCUMENTARY = "Documentary"
    TELEVISION = "Television"

class AchievementType(str, Enum):
    """Types of achievements that can be tracked"""
    AWARD = "Award"
    PRODUCTION_CREDIT = "Production Credit"
    FESTIVAL_SELECTION = "Festival Selection"
    REVIEW = "Review/Reception"
    INDUSTRY_RECOGNITION = "Industry Recognition"

class ProjectType(str, Enum):
    """Types of film/TV projects"""
    FEATURE_FILM = "Feature Film"
    SHORT_FILM = "Short Film"
    TV_SERIES = "TV Series"
    TV_MOVIE = "TV Movie"
    WEB_SERIES = "Web Series"
    DOCUMENTARY = "Documentary"
    ANIMATION = "Animation"

class PrivacySettings(BaseModel):
    """Privacy preferences for alumni profiles"""
    public_profile: bool = True
    show_email: bool = False
    allow_notifications: bool = True
    show_achievements: bool = True

class Alumni(BaseModel):
    """Alumni data model with validation"""
    id: int
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the alumnus")
    graduation_year: int = Field(..., ge=1970, le=2025, description="Year of graduation")
    degree_program: DegreeProgram
    email: Optional[str] = Field(None, description="Contact email address")
    linkedin_url: Optional[str] = None
    imdb_url: Optional[str] = None
    website: Optional[str] = None
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email address')
        return v
    
    @validator('linkedin_url', 'imdb_url', 'website')
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class Achievement(BaseModel):
    """Achievement tracking model"""
    id: int
    alumni_id: int
    type: AchievementType
    title: str = Field(..., min_length=3, max_length=200)
    date: date
    description: str = Field(..., max_length=1000)
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    verified: bool = Field(False, description="Manual verification status")
    source: str = Field(..., description="Data source for this achievement")
    source_url: Optional[str] = None
    project_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        return round(v, 2)

class Project(BaseModel):
    """Film/TV project model"""
    id: int
    title: str = Field(..., min_length=1, max_length=200)
    release_date: Optional[date] = None
    type: ProjectType
    imdb_id: Optional[str] = None
    tmdb_id: Optional[str] = None
    streaming_platforms: List[str] = Field(default_factory=list)
    poster_url: Optional[str] = None
    synopsis: Optional[str] = None
    runtime_minutes: Optional[int] = Field(None, ge=1)
    budget: Optional[float] = None
    box_office: Optional[float] = None
    
    @validator('imdb_id')
    def validate_imdb_id(cls, v):
        if v and not v.startswith('tt'):
            raise ValueError('IMDB ID must start with "tt"')
        return v

class AlumniProject(BaseModel):
    """Many-to-many relationship between alumni and projects"""
    alumni_id: int
    project_id: int
    role: str = Field(..., description="Role in the project (e.g., Director, Producer)")
    character_name: Optional[str] = Field(None, description="Character name if actor")
    billing_order: Optional[int] = Field(None, ge=1, description="Billing position")
    verified_status: bool = False
    notes: Optional[str] = None

class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    total_alumni: int
    total_achievements: int
    total_projects: int = 0
    recent_achievements: List[Dict[str, Any]]
    achievements_by_year: Dict[int, int]
    achievements_by_type: Dict[str, int] = {}
    top_achievers: List[Dict[str, Any]]
    trending_projects: List[Dict[str, Any]] = []

class DataSource(BaseModel):
    """External data source configuration"""
    name: str
    type: str  # API, RSS, Web Scraping
    url: str
    active: bool = True
    rate_limit: int = Field(60, description="Requests per hour")
    api_key: Optional[str] = None
    last_checked: Optional[datetime] = None
    last_error: Optional[str] = None
    success_rate: float = Field(1.0, ge=0.0, le=1.0)
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['API', 'RSS', 'Web Scraping']
        if v not in valid_types:
            raise ValueError(f'Type must be one of: {", ".join(valid_types)}')
        return v

class SearchQuery(BaseModel):
    """Search parameters for alumni or achievements"""
    query: str = Field(..., min_length=1)
    graduation_year_min: Optional[int] = None
    graduation_year_max: Optional[int] = None
    degree_program: Optional[DegreeProgram] = None
    achievement_type: Optional[AchievementType] = None
    verified_only: bool = False
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)

class WebhookEvent(BaseModel):
    """Webhook event for real-time updates"""
    event_type: str  # achievement_added, alumni_updated, etc.
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]
    source: str
    
class SystemConfig(BaseModel):
    """System configuration settings"""
    update_frequency_hours: int = Field(24, ge=1)
    ai_confidence_threshold: float = Field(0.8, ge=0.0, le=1.0)
    max_api_retries: int = Field(3, ge=1)
    enable_notifications: bool = True
    dashboard_refresh_seconds: int = Field(300, ge=30)
    backup_retention_days: int = Field(90, ge=7)