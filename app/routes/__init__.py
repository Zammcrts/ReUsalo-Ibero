from fastapi import APIRouter

from app.routes import auth, catalog, offers, posts, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(posts.router)
api_router.include_router(offers.router)
