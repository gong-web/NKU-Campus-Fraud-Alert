"""v1 路由聚合点。"""

from fastapi import APIRouter

from app.api.v1 import _examples, audit, auth, drafts, fraud_types, judicial, reports, users


def build_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(auth.router)
    router.include_router(users.router)
    router.include_router(audit.router)
    router.include_router(judicial.router)
    # UC-01 / UC-02：上报 + 草稿 + 诈骗类型字典
    router.include_router(fraud_types.router)
    router.include_router(reports.router)
    router.include_router(drafts.router)
    router.include_router(_examples.router)
    return router
