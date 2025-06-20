import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Date, Boolean, Text, DECIMAL, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
import enum
from typing import AsyncGenerator

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://alumdash_user:secure_alumdash_2025@localhost:5432/alumdash")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()

# Enum definitions matching PostgreSQL enums
class DegreeProgram(enum.Enum):
    FILM_PRODUCTION = "Film Production"
    SCREENWRITING = "Screenwriting"
    ANIMATION = "Animation"
    DOCUMENTARY = "Documentary"
    TELEVISION = "Television"

class AchievementType(enum.Enum):
    AWARD = "Award"
    PRODUCTION_CREDIT = "Production Credit"
    FESTIVAL_SELECTION = "Festival Selection"
    REVIEW = "Review/Reception"
    INDUSTRY_RECOGNITION = "Industry Recognition"

class ProjectType(enum.Enum):
    FEATURE_FILM = "Feature Film"
    SHORT_FILM = "Short Film"
    TV_SERIES = "TV Series"
    TV_MOVIE = "TV Movie"
    WEB_SERIES = "Web Series"
    DOCUMENTARY = "Documentary"
    ANIMATION = "Animation"

class DataSourceType(enum.Enum):
    API = "API"
    RSS = "RSS"
    WEB_SCRAPING = "Web Scraping"

# SQLAlchemy Models
class Alumni(Base):
    __tablename__ = "alumni"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    graduation_year = Column(Integer, nullable=False)
    degree_program = Column(SQLEnum(DegreeProgram, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    email = Column(String(255))
    linkedin_url = Column(Text)
    imdb_url = Column(Text)
    website = Column(Text)
    public_profile = Column(Boolean, default=True)
    show_email = Column(Boolean, default=False)
    allow_notifications = Column(Boolean, default=True)
    show_achievements = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    release_date = Column(Date)
    type = Column(SQLEnum(ProjectType), nullable=False)
    imdb_id = Column(String(20))
    tmdb_id = Column(String(20))
    poster_url = Column(Text)
    synopsis = Column(Text)
    runtime_minutes = Column(Integer)
    budget = Column(DECIMAL(15, 2))
    box_office = Column(DECIMAL(15, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    alumni_id = Column(Integer, ForeignKey("alumni.id"), nullable=False)
    type = Column(SQLEnum(AchievementType), nullable=False)
    title = Column(String(200), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(DECIMAL(3, 2), nullable=False)
    verified = Column(Boolean, default=False)
    source = Column(String(200), nullable=False)
    source_url = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AlumniProject(Base):
    __tablename__ = "alumni_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    alumni_id = Column(Integer, ForeignKey("alumni.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    role = Column(String(100), nullable=False)
    character_name = Column(String(100))
    billing_order = Column(Integer)
    verified_status = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ImportLog(Base):
    __tablename__ = "import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    import_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="processing")
    total_records = Column(Integer)
    successful_records = Column(Integer)
    failed_records = Column(Integer)
    error_details = Column(JSONB)
    imported_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(SQLEnum(DataSourceType), nullable=False)
    url = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=60)
    api_key_encrypted = Column(Text)
    last_checked = Column(DateTime(timezone=True))
    last_error = Column(Text)
    success_rate = Column(DECIMAL(3, 2), default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ProjectStreamingPlatform(Base):
    __tablename__ = "project_streaming_platforms"
    
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    platform_name = Column(String(100), nullable=False, primary_key=True)

# Dependency to get database session
async def get_database() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database tables (for development)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Health check for database
async def check_database_health() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception:
        return False
