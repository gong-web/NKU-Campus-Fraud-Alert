"""种子数据：5 院系 + 角色 + 权限矩阵 + 测试账号。

执行：``python -m app.infra.db.seed`` 或 ``make seed``。

幂等：每条 INSERT 都先 SELECT 查重；脚本可重复执行。
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.core.snowflake import next_snowflake_id
from app.infra.cache.rbac_cache import RBACCache
from app.infra.db.models import (
    Department,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.infra.db.models.user import UserStatus
from app.infra.db.session import uow
from app.services import permissions as perm

logger = get_logger(__name__)


# ── 数据 ────────────────────────────────────────────────────────────
DEPARTMENTS: list[dict[str, str | int]] = [
    {"dept_code": "UNKNOWN", "dept_name": "未指定"},
    {"dept_code": "CS", "dept_name": "计算机学院", "sort_order": 1},
    {"dept_code": "MATH", "dept_name": "数学科学学院", "sort_order": 2},
    {"dept_code": "BUSI", "dept_name": "商学院", "sort_order": 3},
    {"dept_code": "FOREIGN", "dept_name": "外国语学院", "sort_order": 4},
    {"dept_code": "PHYS", "dept_name": "物理科学学院", "sort_order": 5},
]

ROLES: list[dict[str, str | int]] = [
    {"role_code": Role.CODE_STUDENT, "role_name": "学生", "role_level": 1},
    {"role_code": Role.CODE_REVIEWER, "role_name": "审核管理员（院系级）", "role_level": 1},
    {"role_code": Role.CODE_REVIEWER, "role_name": "审核管理员（校级）", "role_level": 2},
    {"role_code": Role.CODE_SYS_ADMIN, "role_name": "系统管理员", "role_level": 1},
]

# PRD UC-01：8 类诈骗类型（写入 SystemConfig 暂存；FraudType 表由业务模块负责人建）
FRAUD_TYPES: list[dict[str, str]] = [
    {"type_code": "BRUSH_REWARD", "type_name": "刷单返利类"},
    {"type_code": "FAKE_POLICE", "type_name": "冒充公检法类"},
    {"type_code": "FAKE_JOB", "type_name": "虚假兼职招聘类"},
    {"type_code": "DATING_FRAUD", "type_name": "恋爱交友诈骗类"},
    {"type_code": "FAKE_REFUND", "type_name": "冒充客服退款类"},
    {"type_code": "FAKE_LOAN", "type_name": "虚假网络贷款类"},
    {"type_code": "GAME_TRADE", "type_name": "游戏账号交易诈骗类"},
    {"type_code": "OTHER", "type_name": "其他类型"},
]

TEST_USERS: list[dict[str, str]] = [
    # SysAdmin
    {
        "cas_account": "sysadmin001",
        "real_name": "测试系统管理员",
        "role_code": "SYS_ADMIN",
        "dept_code": "UNKNOWN",
    },
    # Reviewer · 院系级
    {
        "cas_account": "reviewer_dept001",
        "real_name": "计院辅导员-王老师",
        "role_code": "REVIEWER",
        "dept_code": "CS",
    },
    # Reviewer · 校级
    {
        "cas_account": "reviewer_school001",
        "real_name": "保卫处李主任",
        "role_code": "REVIEWER_SCHOOL",
        "dept_code": "UNKNOWN",
    },
    # 学生
    {"cas_account": "student001", "real_name": "张三", "role_code": "STUDENT", "dept_code": "CS"},
    {"cas_account": "student002", "real_name": "李四", "role_code": "STUDENT", "dept_code": "MATH"},
    {"cas_account": "student003", "real_name": "王五", "role_code": "STUDENT", "dept_code": "BUSI"},
    {
        "cas_account": "student004",
        "real_name": "赵六",
        "role_code": "STUDENT",
        "dept_code": "FOREIGN",
    },
    {"cas_account": "student005", "real_name": "钱七", "role_code": "STUDENT", "dept_code": "PHYS"},
]


async def seed_all() -> None:  # noqa: C901 - seed 脚本按步骤串行更容易审计
    async with uow() as session:
        # 1. 院系
        for dept_data in DEPARTMENTS:
            existing_dept = (
                await session.execute(
                    select(Department).where(Department.dept_code == dept_data["dept_code"])
                )
            ).scalar_one_or_none()
            if existing_dept is None:
                session.add(Department(**dept_data))
        await session.flush()

        # 2. 角色
        for role_data in ROLES:
            existing_role = (
                await session.execute(
                    select(Role).where(
                        Role.role_code == role_data["role_code"],
                        Role.role_level == role_data["role_level"],
                    )
                )
            ).scalar_one_or_none()
            if existing_role is None:
                session.add(Role(**role_data))
        await session.flush()

        # 3. 权限码
        for code in sorted(perm.all_permission_codes()):
            existing = (
                await session.execute(select(Permission).where(Permission.permission_code == code))
            ).scalar_one_or_none()
            if existing is None:
                resource, action = code.split(":", 1)
                session.add(
                    Permission(
                        permission_code=code,
                        permission_name=code,  # 中文 PR 由后续补
                        resource_type=resource.upper(),
                        action_type=action.upper(),
                    )
                )
        await session.flush()

        # 4. 角色权限矩阵
        roles_by_code: dict[str, list[Role]] = {}
        for role_obj in (await session.execute(select(Role))).scalars():
            roles_by_code.setdefault(role_obj.role_code, []).append(role_obj)
        perms_by_code = {
            p.permission_code: p for p in (await session.execute(select(Permission))).scalars()
        }
        existing_pairs = {
            (rp.role_id, rp.permission_id)
            for rp in (await session.execute(select(RolePermission))).scalars()
        }
        for role_code, codes in perm.ROLE_PERMISSIONS_DEFAULT.items():
            for role_obj in roles_by_code.get(role_code, []):
                for code in codes:
                    p = perms_by_code.get(code)
                    if p is None:
                        continue
                    if (role_obj.role_id, p.permission_id) in existing_pairs:
                        continue
                    session.add(
                        RolePermission(
                            role_id=role_obj.role_id,
                            permission_id=p.permission_id,
                        )
                    )
        await session.flush()

        # 5. 测试账号
        student_role = next(
            (r for r in roles_by_code.get("STUDENT", []) if r.role_level == 1), None
        )
        reviewer_dept_role = next(
            (r for r in roles_by_code.get("REVIEWER", []) if r.role_level == 1), None
        )
        reviewer_school_role = next(
            (r for r in roles_by_code.get("REVIEWER", []) if r.role_level == 2), None
        )
        sysadmin_role = roles_by_code.get("SYS_ADMIN", [None])[0]

        depts_by_code = {
            d.dept_code: d for d in (await session.execute(select(Department))).scalars()
        }

        def role_for(code: str) -> Role | None:
            return {
                "STUDENT": student_role,
                "REVIEWER": reviewer_dept_role,
                "REVIEWER_SCHOOL": reviewer_school_role,
                "SYS_ADMIN": sysadmin_role,
            }.get(code)

        for user_data in TEST_USERS:
            existing_user = (
                await session.execute(
                    select(User).where(User.cas_account == user_data["cas_account"])
                )
            ).scalar_one_or_none()
            if existing_user is not None:
                continue
            role = role_for(user_data["role_code"])
            dept = depts_by_code.get(user_data["dept_code"])
            if role is None or dept is None:
                continue
            session.add(
                User(
                    user_id=next_snowflake_id(),
                    cas_account=user_data["cas_account"],
                    real_name=user_data["real_name"],
                    department_id=dept.dept_id,
                    role_id=role.role_id,
                    status=UserStatus.ACTIVE.value,
                )
            )
        await session.flush()
        logger.info("seed_users_done")

    # 6. RBAC 缓存预热
    async with uow() as session:
        from app.infra.repositories.role import RoleRepository

        roles_repo = RoleRepository(session)
        mapping = await roles_repo.list_role_permissions_full()
    await RBACCache().load(mapping)
    logger.info("seed_done", departments=len(DEPARTMENTS), users=len(TEST_USERS))


async def _main() -> None:
    configure_logging(level="INFO")
    await seed_all()


if __name__ == "__main__":
    asyncio.run(_main())
