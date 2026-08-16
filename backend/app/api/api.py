from fastapi import APIRouter
from app.api import auth, knowledge_sources

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(knowledge_sources.router)
