# Routers package
from app.routers.auth import router as auth_router
from app.routers.cases import router as cases_router
from app.routers.verdicts import router as verdicts_router
from app.routers.feedback import router as feedback_router
from app.routers.agents import router as agents_router
from app.routers.dashboard import router as dashboard_router
from app.routers.domains import router as domains_router

__all__ = [
    "auth_router",
    "cases_router",
    "verdicts_router",
    "feedback_router",
    "agents_router",
    "dashboard_router",
    "domains_router",
]
