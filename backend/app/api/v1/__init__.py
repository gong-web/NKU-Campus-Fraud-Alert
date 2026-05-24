"""v1 路由聚合点。"""

from fastapi import APIRouter

from app.api.v1 import (
    _examples,
    admin_knowledge,
    admin_quiz,
    admin_reports,
    admin_warnings,
    audit,
    auth,
    departments,
    drafts,
    fraud_types,
    judicial,
    knowledge,
    notifications,
    quiz,
    reports,
    users,
    warnings,
)


def build_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(auth.router)
    router.include_router(users.router)
    router.include_router(audit.router)
    router.include_router(judicial.router)
    router.include_router(admin_reports.router)
    # UC-01 / UC-02：上报 + 草稿 + 诈骗类型字典
    router.include_router(fraud_types.router)
    router.include_router(reports.router)
    router.include_router(drafts.router)
    # 通用字典：院系
    router.include_router(departments.router)
    # UC-03 / UC-07：预警公告
    router.include_router(warnings.router)
    router.include_router(admin_warnings.router)
    # UC-04 / UC-08：知识库
    router.include_router(knowledge.router)
    router.include_router(admin_knowledge.router)
    # UC-05 / UC-09：安全测验（题库、随机练习、指定测验、完成率报告）
    router.include_router(quiz.router)
    router.include_router(admin_quiz.router)
    # 公共组件：站内通知中心（被审核 / 预警 / 知识库 / 测验 全员调用）
    router.include_router(notifications.router)
    router.include_router(_examples.router)
    return router
