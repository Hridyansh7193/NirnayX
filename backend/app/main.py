from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.routers import (
    auth_router,
    cases_router,
    verdicts_router,
    feedback_router,
    agents_router,
    dashboard_router,
    domains_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield
    # Shutdown logic can go here

# Create FastAPI application
app = FastAPI(
    title="NirnayX API",
    description=(
        "NirnayX is an AI-powered, reinforcement learning-based jury simulation engine "
        "that transforms complex, multi-stakeholder decisions into transparent, adaptive, "
        "and explainable verdicts."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(verdicts_router)
app.include_router(feedback_router)
app.include_router(agents_router)
app.include_router(dashboard_router)
app.include_router(domains_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "NirnayX API",
        "version": "1.0.0",
        "description": "Reinforcement Learning-Based Jury Decision Platform",
        "docs": "/docs",
        "health": "/api/v1/dashboard/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
