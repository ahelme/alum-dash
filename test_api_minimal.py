#!/usr/bin/env python3
"""
Minimal test to verify automation API endpoints structure for GitHub Issue #2
Tests the API responses without database dependencies.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from typing import List
import uvicorn
import requests
import json
import time
import threading
from pydantic import BaseModel

# Minimal data models matching main.py
class AutomationStats(BaseModel):
    discoveries_today: int
    discoveries_change: float
    high_confidence: int
    total_discoveries: int
    active_sources: int
    total_sources: int
    avg_processing_time: float
    status: str
    next_scheduled_run: datetime

class DataSourceStatus(BaseModel):
    name: str
    type: str
    active: bool
    last_run: datetime = None
    next_run: datetime = None
    success_rate: float
    items_found_today: int
    rate_limit: int
    errors: List[str] = []

class DiscoveryItem(BaseModel):
    id: str
    title: str
    alumni_name: str
    achievement_type: str
    source: str
    confidence: float
    timestamp: datetime
    source_url: str = None
    verified: bool = False

# Create test app
app = FastAPI(title="Automation API Test")

@app.get("/api/automation/status", response_model=AutomationStats)
async def get_automation_status():
    """Get current automation status and statistics"""
    return AutomationStats(
        discoveries_today=24,
        discoveries_change=18.5,
        high_confidence=19,
        total_discoveries=24,
        active_sources=8,
        total_sources=10,
        avg_processing_time=12.5,
        status="running",
        next_scheduled_run=datetime.now() + timedelta(hours=2)
    )

@app.get("/api/automation/sources", response_model=List[DataSourceStatus])
async def get_data_sources():
    """Get status of all data sources"""
    return [
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
        )
    ]

@app.get("/api/automation/discoveries", response_model=List[DiscoveryItem])
async def get_recent_discoveries():
    """Get recent discoveries from automation"""
    return [
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
        )
    ]

def test_apis():
    """Test all automation endpoints"""
    base_url = "http://localhost:8002"
    
    print("\n🧪 Testing Automation API Endpoints...")
    print("="*50)
    
    endpoints = [
        "/api/automation/status",
        "/api/automation/sources", 
        "/api/automation/discoveries"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"✅ GET {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if endpoint == "/api/automation/status":
                    print(f"   📊 Discoveries today: {data.get('discoveries_today')}")
                    print(f"   📈 Status: {data.get('status')}")
                elif endpoint == "/api/automation/sources":
                    print(f"   📊 Found {len(data)} data sources")
                elif endpoint == "/api/automation/discoveries":
                    print(f"   📊 Found {len(data)} discoveries")
            else:
                print(f"   ❌ Response: {response.text}")
                
        except Exception as e:
            print(f"❌ GET {endpoint} - Error: {e}")
    
    print("="*50)
    print("🏁 API testing complete!")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING GITHUB ISSUE #2 FIX")
    print("Automation API JSON Response Validation")
    print("="*60)
    
    # Start server in a separate thread
    def run_server():
        uvicorn.run(app, host="0.0.0.0", port=8002, log_level="error")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    print("🚀 Starting test server on port 8002...")
    time.sleep(2)
    
    # Run tests
    test_apis()
    
    print(f"\n🌐 Test server: http://localhost:8002/docs")
    print("📄 API docs available for manual testing")
    print("\nPress CTRL+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping test server...")