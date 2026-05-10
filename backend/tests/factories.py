"""factory_boy 测试数据工厂。

组员需要测试数据时，无脑一行：

.. code-block:: python

    user = await UserFactory.create_async(session)
    user_admin = await UserFactory.create_async(session, role_id=4)

任何字段可被 kwargs 覆盖。
"""

from __future__ import annotations

import factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.snowflake import next_snowflake_id
from app.infra.db.models import Department, Role, User
from app.infra.db.models.user import UserStatus


class _AsyncFactoryMixin:
    """帮 factory_boy 走 async ``session.add`` + ``flush``。"""

    @classmethod
    async def create_async(cls, session: AsyncSession, **kwargs: object):  # type: ignore[no-untyped-def]
        obj = cls.build(**kwargs)  # type: ignore[attr-defined]
        session.add(obj)
        await session.flush()
        return obj


class DepartmentFactory(_AsyncFactoryMixin, factory.Factory):
    class Meta:
        model = Department

    dept_code = factory.Sequence(lambda n: f"D{n:03d}")
    dept_name = factory.Sequence(lambda n: f"测试院系{n}")
    dept_level = 1


class RoleFactory(_AsyncFactoryMixin, factory.Factory):
    class Meta:
        model = Role

    role_code = "STUDENT"
    role_name = "学生"
    role_level = 1


class UserFactory(_AsyncFactoryMixin, factory.Factory):
    class Meta:
        model = User

    user_id = factory.LazyFunction(next_snowflake_id)
    cas_account = factory.Sequence(lambda n: f"u{n:05d}")
    real_name = factory.Sequence(lambda n: f"测试用户{n}")
    department_id = 1
    role_id = 1
    status = UserStatus.ACTIVE.value
