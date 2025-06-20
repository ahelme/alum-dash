#!/usr/bin/env python3
"""
Test script to verify automation API endpoints work correctly for GitHub Issue #2
This tests that frontend can successfully communicate with backend automation APIs.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from main import app  # Import the main app
import uvicorn
import requests
import json
import time
import threading

def test_automation_apis():
    """Test all automation endpoints"""
    base_url = "http://localhost:8001"  # Use different port to avoid conflicts
    
    print("\n🧪 Testing Automation API Endpoints...")
    print("="*50)
    
    # Test 1: Status endpoint
    try:
        response = requests.get(f"{base_url}/api/automation/status")
        print(f"✅ GET /api/automation/status - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Discoveries today: {data.get('discoveries_today')}")
            print(f"   📈 Status: {data.get('status')}")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/automation/status - Error: {e}")
    
    # Test 2: Sources endpoint
    try:
        response = requests.get(f"{base_url}/api/automation/sources")
        print(f"✅ GET /api/automation/sources - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Found {len(data)} data sources")
            for source in data:
                print(f"   • {source['name']} ({source['type']}) - Active: {source['active']}")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/automation/sources - Error: {e}")
    
    # Test 3: Discoveries endpoint  
    try:
        response = requests.get(f"{base_url}/api/automation/discoveries")
        print(f"✅ GET /api/automation/discoveries - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Found {len(data)} discoveries")
            for discovery in data[:2]:  # Show first 2
                print(f"   • {discovery['title']} by {discovery['alumni_name']} (confidence: {discovery['confidence']})")
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/automation/discoveries - Error: {e}")
    
    # Test 4: Toggle endpoint
    try:
        toggle_data = {"action": "start"}
        response = requests.post(f"{base_url}/api/automation/toggle", json=toggle_data)
        print(f"✅ POST /api/automation/toggle - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ POST /api/automation/toggle - Error: {e}")
    
    # Test 5: Manual run endpoint
    try:
        response = requests.post(f"{base_url}/api/automation/manual-run", json={})
        print(f"✅ POST /api/automation/manual-run - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"❌ POST /api/automation/manual-run - Error: {e}")
    
    print("="*50)
    print("🏁 Automation API testing complete!")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING GITHUB ISSUE #2 FIX")
    print("Frontend-Backend API Integration for Automation")
    print("="*60)
    
    # Start server in a separate thread
    def run_server():
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    print("🚀 Starting test server on port 8001...")
    time.sleep(3)
    
    # Run tests
    test_automation_apis()
    
    print("\n🌐 Test server running at http://localhost:8001")
    print("You can also test the frontend there!")
    print("\nPress CTRL+C to stop")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping test server...")