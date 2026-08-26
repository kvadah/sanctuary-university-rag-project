from fastapi import APIRouter
from app.api import auth, knowledge_sources, documents, chat, analytics

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(knowledge_sources.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(analytics.router)
