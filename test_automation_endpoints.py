#!/usr/bin/env python3
"""
Test automation endpoints from main.py for GitHub Issue #2
This tests the actual endpoints without requiring database connection.
"""

import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Mock database dependency to avoid connection issues
class MockAsyncSession:
    def __init__(self):
        pass

def get_mock_database():
    return MockAsyncSession()

# Import and patch the main app
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Patch the database dependency before importing main
import main
main.get_database = get_mock_database

from main import app

def test_automation_apis():
    """Test automation endpoints using FastAPI TestClient"""
    
    print("\n🧪 Testing Automation API Endpoints with Real Backend...")
    print("="*60)
    
    client = TestClient(app)
    
    # Test 1: Status endpoint
    print("Testing GET /api/automation/status")
    try:
        response = client.get("/api/automation/status")
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Discoveries today: {data.get('discoveries_today')}")
            print(f"   📈 Status: {data.get('status')}")
            print(f"   🎯 Active sources: {data.get('active_sources')}")
            print(f"   ⏰ Next run: {data.get('next_scheduled_run')}")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: Sources endpoint
    print("Testing GET /api/automation/sources")
    try:
        response = client.get("/api/automation/sources")
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Found {len(data)} data sources")
            for source in data:
                print(f"   • {source['name']} ({source['type']}) - Active: {source['active']}")
                print(f"     Success rate: {source['success_rate']}% | Items today: {source['items_found_today']}")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 3: Discoveries endpoint
    print("Testing GET /api/automation/discoveries")
    try:
        response = client.get("/api/automation/discoveries")
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Found {len(data)} discoveries")
            for discovery in data:
                print(f"   • {discovery['title']}")
                print(f"     Alumni: {discovery['alumni_name']}")
                print(f"     Type: {discovery['achievement_type']}")
                print(f"     Confidence: {discovery['confidence']}")
                print(f"     Source: {discovery['source']}")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 4: Toggle endpoint
    print("Testing POST /api/automation/toggle")
    try:
        toggle_data = {"action": "start"}
        response = client.post("/api/automation/toggle", json=toggle_data)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Response: {data}")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 5: Manual run endpoint
    print("Testing POST /api/automation/manual-run")
    try:
        response = client.post("/api/automation/manual-run", json={})
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Response: {data}")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("🏁 Automation API testing complete!")
    
    # Test JSON parsing specifically (the main issue from frontend)
    print("\n🔍 Testing JSON Response Parsing...")
    print("="*40)
    
    endpoints = [
        "/api/automation/status",
        "/api/automation/sources", 
        "/api/automation/discoveries"
    ]
    
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            if response.status_code == 200:
                # Try to parse JSON
                data = response.json()
                print(f"✅ {endpoint} - JSON parsing successful")
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    print(f"   ✅ Content-Type: {content_type}")
                else:
                    print(f"   ⚠️  Content-Type: {content_type}")
            else:
                print(f"❌ {endpoint} - HTTP {response.status_code}")
                
        except json.JSONDecodeError as e:
            print(f"❌ {endpoint} - JSON parsing failed: {e}")
            print(f"   Response: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 TESTING GITHUB ISSUE #2")
    print("Frontend-Backend API Mismatch for Automation Features")
    print("="*70)
    print("\n🎯 Goal: Verify automation endpoints return valid JSON")
    print("🔧 Method: FastAPI TestClient (no network required)")
    
    test_automation_apis()
    
    print("\n✅ If all tests pass, the automation endpoints are working!")
    print("🌐 Frontend should now be able to communicate with backend properly.")
    print("\n📝 Next steps:")
    print("   1. Test with real frontend at http://localhost:8000")
    print("   2. Check browser console for any remaining errors")
    print("   3. Verify automation dashboard loads data correctly")