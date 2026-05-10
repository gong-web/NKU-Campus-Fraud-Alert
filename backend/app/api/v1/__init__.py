"""v1 路由聚合点。"""

from fastapi import APIRouter

from app.api.v1 import _examples, audit, auth, judicial, users


def build_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(auth.router)
    router.include_router(users.router)
    router.include_router(audit.router)
    router.include_router(judicial.router)
    router.include_router(_examples.router)
    return router
