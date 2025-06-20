from datetime import date, datetime
from typing import List, Optional, Dict
from models import (
    Alumni, Achievement, Project, AlumniProject,
    DegreeProgram, AchievementType, ProjectType, PrivacySettings
)

# Mock database - In production, this would be PostgreSQL
mock_alumni: List[Alumni] = [
    Alumni(
        id=1,
        name="Sarah Chen",
        graduation_year=2018,
        degree_program=DegreeProgram.FILM_PRODUCTION,
        email="s.chen@example.com",
        linkedin_url="https://linkedin.com/in/sarahchen",
        imdb_url="https://www.imdb.com/name/nm1234567",
        privacy_settings=PrivacySettings()
    ),
    Alumni(
        id=2,
        name="James Mitchell",
        graduation_year=2020,
        degree_program=DegreeProgram.DOCUMENTARY,
        email="j.mitchell@example.com",
        website="https://jamesmitchellfilms.com",
        privacy_settings=PrivacySettings(show_email=True)
    ),
    Alumni(
        id=3,
        name="Emma Rodriguez",
        graduation_year=2019,
        degree_program=DegreeProgram.ANIMATION,
        email="e.rodriguez@example.com",
        linkedin_url="https://linkedin.com/in/emmarodriguez",
        privacy_settings=PrivacySettings()
    ),
    Alumni(
        id=4,
        name="Michael O'Brien",
        graduation_year=2017,
        degree_program=DegreeProgram.SCREENWRITING,
        email="m.obrien@example.com",
        imdb_url="https://www.imdb.com/name/nm2345678",
        privacy_settings=PrivacySettings()
    ),
    Alumni(
        id=5,
        name="Priya Sharma",
        graduation_year=2021,
        degree_program=DegreeProgram.TELEVISION,
        email="p.sharma@example.com",
        privacy_settings=PrivacySettings(public_profile=False)
    )
]

mock_projects: List[Project] = [
    Project(
        id=1,
        title="Silent Echoes",
        release_date=date(2024, 6, 15),
        type=ProjectType.SHORT_FILM,
        imdb_id="tt1234567",
        tmdb_id="123456",
        runtime_minutes=15,
        synopsis="A haunting exploration of memory and loss in modern Melbourne."
    ),
    Project(
        id=2,
        title="Urban Voices",
        release_date=date(2024, 3, 10),
        type=ProjectType.DOCUMENTARY,
        runtime_minutes=90,
        streaming_platforms=["Netflix", "Stan"],
        synopsis="Documentary exploring the diverse communities of Australian cities."
    ),
    Project(
        id=3,
        title="Dream Weavers",
        release_date=date(2023, 9, 1),
        type=ProjectType.TV_SERIES,
        streaming_platforms=["Netflix"],
        synopsis="An animated series about children who can enter each other's dreams."
    ),
    Project(
        id=4,
        title="The Last Station",
        release_date=date(2023, 11, 20),
        type=ProjectType.FEATURE_FILM,
        imdb_id="tt3456789",
        runtime_minutes=120,
        budget=2500000,
        box_office=8750000
    )
]

mock_achievements: List[Achievement] = [
    Achievement(
        id=1,
        alumni_id=1,
        type=AchievementType.AWARD,
        title="AACTA Award - Best Short Film",
        date=date(2024, 12, 1),
        description="Won AACTA Award for Best Short Film for 'Silent Echoes'",
        confidence_score=0.95,
        verified=True,
        source="AACTA Official Website",
        source_url="https://www.aacta.org/winners",
        project_id=1
    ),
    Achievement(
        id=2,
        alumni_id=2,
        type=AchievementType.FESTIVAL_SELECTION,
        title="Sundance Film Festival - Official Selection",
        date=date(2024, 1, 20),
        description="Documentary 'Urban Voices' selected for Sundance 2024",
        confidence_score=0.90,
        verified=True,
        source="Sundance Institute",
        source_url="https://www.sundance.org",
        project_id=2
    ),
    Achievement(
        id=3,
        alumni_id=3,
        type=AchievementType.PRODUCTION_CREDIT,
        title="Lead Animator - 'Dream Weavers'",
        date=date(2023, 6, 15),
        description="Lead animator on Netflix animated series",
        confidence_score=0.88,
        verified=False,
        source="TMDb API",
        project_id=3
    ),
    Achievement(
        id=4,
        alumni_id=1,
        type=AchievementType.FESTIVAL_SELECTION,
        title="Melbourne International Film Festival - Premiere",
        date=date(2024, 8, 10),
        description="World premiere of 'Silent Echoes' at MIFF",
        confidence_score=0.92,
        verified=True,
        source="MIFF Official Program",
        project_id=1
    ),
    Achievement(
        id=5,
        alumni_id=4,
        type=AchievementType.PRODUCTION_CREDIT,
        title="Screenwriter - 'The Last Station'",
        date=date(2023, 11, 20),
        description="Wrote screenplay for feature film starring Hugh Jackman",
        confidence_score=0.85,
        verified=True,
        source="Screen Australia",
        project_id=4
    ),
    Achievement(
        id=6,
        alumni_id=5,
        type=AchievementType.INDUSTRY_RECOGNITION,
        title="Screen Producers Australia - Emerging Producer Award",
        date=date(2024, 5, 15),
        description="Recognized as one of Australia's top emerging producers",
        confidence_score=0.98,
        verified=True,
        source="Screen Producers Australia"
    ),
    Achievement(
        id=7,
        alumni_id=2,
        type=AchievementType.REVIEW,
        title="The Guardian - 5 Star Review",
        date=date(2024, 3, 15),
        description="'Urban Voices' receives critical acclaim from The Guardian",
        confidence_score=0.87,
        verified=True,
        source="The Guardian Australia",
        source_url="https://www.theguardian.com/au",
        project_id=2
    )
]

mock_alumni_projects: List[AlumniProject] = [
    AlumniProject(
        alumni_id=1,
        project_id=1,
        role="Director",
        verified_status=True
    ),
    AlumniProject(
        alumni_id=2,
        project_id=2,
        role="Director/Producer",
        verified_status=True
    ),
    AlumniProject(
        alumni_id=3,
        project_id=3,
        role="Lead Animator",
        verified_status=False
    ),
    AlumniProject(
        alumni_id=4,
        project_id=4,
        role="Screenwriter",
        verified_status=True
    )
]

# Database helper functions
def get_alumni_by_id(alumni_id: int) -> Optional[Alumni]:
    """Get alumni by ID"""
    return next((a for a in mock_alumni if a.id == alumni_id), None)

def create_alumni_record(alumni: Alumni) -> Alumni:
    """Create new alumni record"""
    alumni.id = len(mock_alumni) + 1
    alumni.created_at = datetime.now()
    alumni.updated_at = datetime.now()
    mock_alumni.append(alumni)
    return alumni

def get_achievements_by_alumni(alumni_id: int) -> List[Achievement]:
    """Get all achievements for specific alumni"""
    return [a for a in mock_achievements if a.alumni_id == alumni_id]

def create_achievement_record(achievement: Achievement) -> Achievement:
    """Create new achievement record"""
    achievement.id = len(mock_achievements) + 1
    achievement.created_at = datetime.now()
    mock_achievements.append(achievement)
    return achievement

def get_project_by_id(project_id: int) -> Optional[Project]:
    """Get project by ID"""
    return next((p for p in mock_projects if p.id == project_id), None)

def get_alumni_projects(alumni_id: int) -> List[Dict]:
    """Get all projects for specific alumni"""
    alumni_project_links = [ap for ap in mock_alumni_projects if ap.alumni_id == alumni_id]
    result = []
    for link in alumni_project_links:
        project = get_project_by_id(link.project_id)
        if project:
            result.append({
                "project": project,
                "role": link.role,
                "verified": link.verified_status
            })
    return result

def search_alumni(query: str) -> List[Alumni]:
    """Search alumni by name"""
    query_lower = query.lower()
    return [a for a in mock_alumni if query_lower in a.name.lower()]

def get_achievements_by_type(achievement_type: AchievementType) -> List[Achievement]:
    """Get achievements filtered by type"""
    return [a for a in mock_achievements if a.type == achievement_type]

def get_recent_achievements(limit: int = 10) -> List[Achievement]:
    """Get most recent achievements"""
    sorted_achievements = sorted(mock_achievements, key=lambda x: x.date, reverse=True)
    return sorted_achievements[:limit]

def get_unverified_achievements() -> List[Achievement]:
    """Get achievements that need verification"""
    return [a for a in mock_achievements if not a.verified and a.confidence_score < 0.9]
