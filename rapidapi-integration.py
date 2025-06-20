"""
RapidAPI Integration for VCA Alumni Tracker
==========================================

Integration with popular movie/entertainment APIs from RapidAPI for enhanced
alumni achievement tracking and movie data collection.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class RapidAPISource(Enum):
    """Available RapidAPI sources for movie data"""
    IMDB_API = "imdb_api"
    MOVIE_DATABASE = "movie_database_alternative"
    STREAMING_AVAILABILITY = "streaming_availability"
    BOXOFFICE = "boxoffice"
    WATCHMODE = "watchmode"
    CINEMA_API = "cinema_api"
    MOVIESMINIDATABASE = "movies_mini_database"

@dataclass
class RapidAPIConfig:
    """Configuration for RapidAPI services"""
    api_key: str
    base_url: str
    rate_limit: int  # requests per minute
    cost_per_request: float  # in USD
    free_tier_limit: int  # free requests per month

# Popular Movie APIs on RapidAPI
RAPIDAPI_SERVICES = {
    RapidAPISource.IMDB_API: RapidAPIConfig(
        api_key="your_rapidapi_key",
        base_url="https://imdb-api1.p.rapidapi.com",
        rate_limit=100,
        cost_per_request=0.001,  # $0.001 per request
        free_tier_limit=1000
    ),
    RapidAPISource.MOVIE_DATABASE: RapidAPIConfig(
        api_key="your_rapidapi_key", 
        base_url="https://moviesdatabase.p.rapidapi.com",
        rate_limit=500,
        cost_per_request=0.0005,
        free_tier_limit=100
    ),
    RapidAPISource.STREAMING_AVAILABILITY: RapidAPIConfig(
        api_key="your_rapidapi_key",
        base_url="https://streaming-availability.p.rapidapi.com",
        rate_limit=100,
        cost_per_request=0.01,
        free_tier_limit=100
    ),
    RapidAPISource.WATCHMODE: RapidAPIConfig(
        api_key="your_rapidapi_key",
        base_url="https://watchmode.p.rapidapi.com",
        rate_limit=1000,
        cost_per_request=0.002,
        free_tier_limit=1000
    ),
    RapidAPISource.MOVIESMINIDATABASE: RapidAPIConfig(
        api_key="your_rapidapi_key",
        base_url="https://movies-mini-database.p.rapidapi.com",
        rate_limit=500,
        cost_per_request=0.001,
        free_tier_limit=1000
    )
}

class RapidAPICollector:
    """Enhanced collector using RapidAPI services"""
    
    def __init__(self, rapidapi_key: str):
        self.rapidapi_key = rapidapi_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_person_imdb(self, name: str) -> List[Dict]:
        """Search for person using IMDB API via RapidAPI"""
        try:
            url = f"{RAPIDAPI_SERVICES[RapidAPISource.IMDB_API].base_url}/searchPerson"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "imdb-api1.p.rapidapi.com"
            }
            
            params = {
                "query": name,
                "limit": 10
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    logger.error(f"IMDB API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching IMDB for {name}: {e}")
            return []

    async def get_person_credits_imdb(self, person_id: str) -> List[Dict]:
        """Get person's filmography using IMDB API"""
        try:
            url = f"{RAPIDAPI_SERVICES[RapidAPISource.IMDB_API].base_url}/person"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "imdb-api1.p.rapidapi.com"
            }
            
            params = {"id": person_id}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Combine acting and directing credits
                    credits = []
                    
                    # Acting credits
                    for credit in data.get('knownFor', []):
                        credits.append({
                            'title': credit.get('title'),
                            'year': credit.get('year'),
                            'role': 'Actor',
                            'character': credit.get('role'),
                            'imdb_id': credit.get('id'),
                            'image': credit.get('image'),
                            'rating': credit.get('imDbRating')
                        })
                    
                    # Directing/producing credits (if available)
                    for credit in data.get('filmography', {}).get('director', []):
                        credits.append({
                            'title': credit.get('title'),
                            'year': credit.get('year'), 
                            'role': 'Director',
                            'imdb_id': credit.get('id')
                        })
                    
                    return credits
                    
        except Exception as e:
            logger.error(f"Error getting IMDB credits for {person_id}: {e}")
            return []

    async def search_movies_database(self, title: str, year: Optional[int] = None) -> List[Dict]:
        """Search movies using Alternative Movie Database API"""
        try:
            url = f"{RAPIDAPI_SERVICES[RapidAPISource.MOVIE_DATABASE].base_url}/titles/search/title/{title}"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "moviesdatabase.p.rapidapi.com"
            }
            
            params = {
                "exact": "false",
                "titleType": "movie,tvSeries,short"
            }
            
            if year:
                params["year"] = str(year)
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                    
        except Exception as e:
            logger.error(f"Error searching movie database for {title}: {e}")
            return []

    async def get_streaming_availability(self, imdb_id: str) -> Dict:
        """Get streaming platform availability"""
        try:
            url = f"{RAPIDAPI_SERVICES[RapidAPISource.STREAMING_AVAILABILITY].base_url}/shows/{imdb_id}"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract streaming services
                    streaming_services = []
                    for country_data in data.get('streamingOptions', {}).values():
                        for service_data in country_data:
                            service = service_data.get('service', {}).get('name')
                            if service and service not in streaming_services:
                                streaming_services.append(service)
                    
                    return {
                        'streaming_services': streaming_services,
                        'available_countries': list(data.get('streamingOptions', {}).keys())
                    }
                    
        except Exception as e:
            logger.error(f"Error getting streaming availability for {imdb_id}: {e}")
            return {}

    async def search_box_office_data(self, title: str, year: int) -> Dict:
        """Get box office data for a movie"""
        try:
            # This would use a box office API - example structure
            url = f"{RAPIDAPI_SERVICES[RapidAPISource.BOXOFFICE].base_url}/search"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "boxoffice-api.p.rapidapi.com"
            }
            
            params = {
                "title": title,
                "year": year
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'worldwide_gross': data.get('worldwide_gross'),
                        'domestic_gross': data.get('domestic_gross'),
                        'international_gross': data.get('international_gross'),
                        'budget': data.get('production_budget'),
                        'opening_weekend': data.get('opening_weekend')
                    }
                    
        except Exception as e:
            logger.error(f"Error getting box office data for {title}: {e}")
            return {}

class EnhancedAlumniCollector:
    """Enhanced alumni data collector using multiple RapidAPI sources"""
    
    def __init__(self, rapidapi_key: str):
        self.rapidapi_key = rapidapi_key
        self.collector = RapidAPICollector(rapidapi_key)
        
    async def collect_comprehensive_data(self, alumni_name: str, graduation_year: int) -> Dict:
        """Collect comprehensive data about an alumni from multiple sources"""
        
        async with self.collector:
            # Search for person across multiple databases
            imdb_results = await self.collector.search_person_imdb(alumni_name)
            
            comprehensive_data = {
                'alumni_name': alumni_name,
                'graduation_year': graduation_year,
                'discovered_profiles': [],
                'film_credits': [],
                'streaming_availability': {},
                'box_office_data': {},
                'confidence_score': 0.0,
                'data_sources': []
            }
            
            # Process IMDB results
            for person in imdb_results[:3]:  # Check top 3 matches
                person_id = person.get('id')
                if person_id:
                    # Get detailed credits
                    credits = await self.collector.get_person_credits_imdb(person_id)
                    
                    # Calculate name similarity
                    name_similarity = self._calculate_name_similarity(
                        alumni_name, person.get('title', '')
                    )
                    
                    if name_similarity > 0.7:  # Good match threshold
                        comprehensive_data['discovered_profiles'].append({
                            'source': 'imdb',
                            'profile_id': person_id,
                            'name': person.get('title'),
                            'image': person.get('image'),
                            'similarity_score': name_similarity,
                            'bio': person.get('description')
                        })
                        
                        # Process credits
                        for credit in credits:
                            # Filter by graduation year (only include post-graduation work)
                            credit_year = credit.get('year')
                            if credit_year and int(credit_year) >= graduation_year:
                                
                                # Get additional data for significant works
                                if credit.get('rating') and float(credit.get('rating', 0)) > 7.0:
                                    # Get streaming availability
                                    imdb_id = credit.get('imdb_id')
                                    if imdb_id:
                                        streaming = await self.collector.get_streaming_availability(imdb_id)
                                        credit['streaming_data'] = streaming
                                        
                                        # Get box office data for movies
                                        if credit.get('role') in ['Director', 'Producer']:
                                            box_office = await self.collector.search_box_office_data(
                                                credit.get('title'), int(credit_year)
                                            )
                                            credit['box_office_data'] = box_office
                                
                                comprehensive_data['film_credits'].append(credit)
            
            # Calculate overall confidence score
            comprehensive_data['confidence_score'] = self._calculate_overall_confidence(
                comprehensive_data
            )
            
            comprehensive_data['data_sources'] = ['imdb_rapidapi', 'streaming_availability']
            
            return comprehensive_data

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        from fuzzywuzzy import fuzz
        return fuzz.ratio(name1.lower(), name2.lower()) / 100.0

    def _calculate_overall_confidence(self, data: Dict) -> float:
        """Calculate overall confidence score for the collected data"""
        confidence = 0.0
        
        # Base confidence from profile matches
        if data['discovered_profiles']:
            avg_similarity = sum(p['similarity_score'] for p in data['discovered_profiles']) / len(data['discovered_profiles'])
            confidence += avg_similarity * 0.4
        
        # Credits boost confidence
        if data['film_credits']:
            # More credits = higher confidence
            credits_score = min(len(data['film_credits']) * 0.1, 0.3)
            confidence += credits_score
            
            # High-rated projects boost confidence
            high_rated = [c for c in data['film_credits'] if c.get('rating') and float(c.get('rating', 0)) > 7.0]
            if high_rated:
                confidence += min(len(high_rated) * 0.1, 0.2)
        
        # Recent work boosts confidence
        current_year = datetime.now().year
        recent_credits = [c for c in data['film_credits'] if c.get('year') and current_year - int(c.get('year', 0)) <= 5]
        if recent_credits:
            confidence += 0.1
        
        return min(confidence, 1.0)

# Integration with existing automation system
async def enhanced_alumni_discovery(alumni_list: List, rapidapi_key: str) -> List[Dict]:
    """Enhanced alumni discovery using RapidAPI services"""
    
    collector = EnhancedAlumniCollector(rapidapi_key)
    discoveries = []
    
    for alumni in alumni_list:
        try:
            # Collect comprehensive data
            data = await collector.collect_comprehensive_data(
                alumni.name, alumni.graduation_year
            )
            
            # Convert to achievements
            for credit in data['film_credits']:
                if data['confidence_score'] > 0.5:  # Only high-confidence discoveries
                    achievement = {
                        'title': f"{credit['role']} - {credit['title']}",
                        'alumni_name': alumni.name,
                        'type': 'Production Credit',
                        'date': f"{credit.get('year', datetime.now().year)}-01-01",
                        'source': 'RapidAPI IMDB',
                        'confidence': data['confidence_score'],
                        'source_url': f"https://www.imdb.com/title/{credit.get('imdb_id', '')}",
                        'metadata': {
                            'role': credit['role'],
                            'character': credit.get('character'),
                            'rating': credit.get('rating'),
                            'streaming_data': credit.get('streaming_data', {}),
                            'box_office_data': credit.get('box_office_data', {})
                        }
                    }
                    discoveries.append(achievement)
                    
        except Exception as e:
            logger.error(f"Error processing alumni {alumni.name}: {e}")
    
    return discoveries

# Environment configuration
RAPIDAPI_ENV_CONFIG = """
# Add these to your .env file:

# RapidAPI Configuration
RAPIDAPI_KEY=your_rapidapi_key_here

# Specific API keys (if using multiple)
RAPIDAPI_IMDB_KEY=your_imdb_api_key
RAPIDAPI_STREAMING_KEY=your_streaming_api_key
RAPIDAPI_BOXOFFICE_KEY=your_boxoffice_api_key

# Rate limiting settings
RAPIDAPI_RATE_LIMIT=100  # requests per minute
RAPIDAPI_MONTHLY_BUDGET=50.00  # USD budget limit

# Enable/disable specific APIs
ENABLE_IMDB_API=true
ENABLE_STREAMING_API=true
ENABLE_BOXOFFICE_API=false
"""

if __name__ == "__main__":
    # Example usage
    async def test_rapidapi():
        rapidapi_key = "your_rapidapi_key_here"
        
        # Mock alumni data
        class MockAlumni:
            def __init__(self, name, graduation_year):
                self.name = name
                self.graduation_year = graduation_year
        
        alumni_list = [
            MockAlumni("Chris Hemsworth", 2005),  # Famous example
            MockAlumni("Margot Robbie", 2008),    # Another example
        ]
        
        discoveries = await enhanced_alumni_discovery(alumni_list, rapidapi_key)
        
        print(f"Found {len(discoveries)} discoveries:")
        for discovery in discoveries:
            print(f"- {discovery['title']} (Confidence: {discovery['confidence']:.2%})")
    
    # asyncio.run(test_rapidapi())
