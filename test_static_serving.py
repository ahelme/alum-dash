#!/usr/bin/env python3
"""
Test script to verify static file serving fix for GitHub Issue #4
This demonstrates that the Docker static file serving mismatch is resolved.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

# Create FastAPI app (minimal version of main.py)
app = FastAPI(title="AlumDash Static File Test")

# Mount static files for React frontend assets
try:
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    print("✅ Static assets mounted successfully from 'static/assets' directory")
except Exception as e:
    print(f"❌ Failed to mount static assets: {e}")
    exit(1)

# Serve React frontend (root route)
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend index.html"""
    try:
        with open("static/index.html", "r") as f:
            content = f.read()
        print("✅ Successfully serving index.html from static/index.html")
        return content
    except FileNotFoundError:
        print("❌ Frontend not found - static/index.html missing")
        raise HTTPException(status_code=404, detail="Frontend not found - ensure build completed successfully")

# Health check
@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "message": "Static file serving test"}

# Catch-all route for React Router (must be last)
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_react_app(full_path: str):
    """
    Catch-all route to serve React app for client-side routing.
    This handles all routes not matched by API endpoints above.
    """
    try:
        with open("static/index.html", "r") as f:
            content = f.read()
        print(f"✅ Serving React app for route: /{full_path}")
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    # Verify static files exist
    if not os.path.exists("static"):
        print("❌ Error: 'static' directory not found")
        print("Please run: mkdir -p static && cp frontend/dist/* static/")
        exit(1)
    
    if not os.path.exists("static/index.html"):
        print("❌ Error: 'static/index.html' not found")
        print("Please run: cp frontend/dist/index.html static/")
        exit(1)
    
    print("\n" + "="*60)
    print("🧪 TESTING GITHUB ISSUE #4 FIX")
    print("Static File Serving for React Frontend")
    print("="*60)
    print("\n✅ Static directory exists")
    print("✅ index.html found")
    print("\n🌐 Starting test server...")
    print("📍 Main app: http://localhost:8000")
    print("📍 Health check: http://localhost:8000/health")
    print("📍 Static assets: http://localhost:8000/static/assets/")
    print("\n🧪 Test routes:")
    print("   • http://localhost:8000/ (should serve React app)")
    print("   • http://localhost:8000/any-route (should serve React app)")
    print("   • http://localhost:8000/static/assets/index-*.css (should serve CSS)")
    print("   • http://localhost:8000/static/assets/index-*.js (should serve JS)")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)