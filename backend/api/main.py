"""
FastAPI application entry point for Grok Recruiter API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

app = FastAPI(
    title="Grok Recruiter API",
    description="API for AI-powered candidate sourcing and recruitment",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["api"])


@app.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        API status
    """
    return {"status": "ok", "message": "Grok Recruiter API"}

