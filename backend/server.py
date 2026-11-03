"""
StockSathi - Smart Retail Decision Engine
FastAPI Main Application Server
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
from supabase import Client, create_client

from backend.config import config
from backend.routes.auth_routes import router as auth_router
from backend.routes.inventory_routes import router as inventory_router
from backend.routes.supplier_routes import router as supplier_router
from backend.routes.order_routes import router as order_router
from backend.routes.prediction_routes import router as prediction_router
from backend.routes.analytics_routes import router as analytics_router
from backend.routes.voice_routes import router as voice_router
from backend.routes.support_routes import router as support_router
from backend.routes.subscription_routes import router as subscription_router
from backend.routes.notification_routes import router as notification_router
from backend.routes.demo_routes import router as demo_router

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    description=config.DESCRIPTION
)

supabase_client: Client | None = None
if config.SUPABASE_URL and config.SUPABASE_KEY:
    supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(supplier_router)
app.include_router(order_router)
app.include_router(prediction_router)
app.include_router(analytics_router)
app.include_router(voice_router)
app.include_router(support_router)
app.include_router(subscription_router)
app.include_router(notification_router)
app.include_router(demo_router)

# Static Files & Frontend SPA
frontend_dir = config.FRONTEND_DIR
assets_dir = frontend_dir / "assets"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "StockSathi Decision Engine",
        "version": config.VERSION
    }

@app.get("/test-db")
def test_database_connection():
    if (
        supabase_client is None
        or not config.SUPABASE_KEY
        or config.SUPABASE_KEY == "<YOUR_SUPABASE_KEY>"
    ):
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_configured",
                "detail": "Set a valid SUPABASE_KEY in backend/.env.",
            },
        )

    try:
        response = supabase_client.postgrest.session.get(
            f"{config.SUPABASE_URL.rstrip('/')}/rest/v1/",
            timeout=10,
        )
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=502,
            content={
                "status": "error",
                "detail": f"Could not connect to Supabase: {exc}",
            },
        )

    if not response.is_success:
        return JSONResponse(
            status_code=502,
            content={
                "status": "error",
                "detail": f"Supabase returned HTTP {response.status_code}. Check the URL and API key.",
            },
        )

    return {"status": "connected", "service": "Supabase"}

# SPA Catch-all: serve index.html for frontend routing
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    # If API path not matched, return 404 JSON
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
    
    # Check if a static file in frontend directory exists
    file_candidate = frontend_dir / full_path
    if full_path and file_candidate.is_file():
        return FileResponse(str(file_candidate))
        
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(status_code=404, content={"detail": "Frontend index.html not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host=config.HOST, port=config.PORT, reload=True)
