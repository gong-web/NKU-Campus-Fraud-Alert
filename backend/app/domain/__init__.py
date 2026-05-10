"""领域对象（纯 Python，不依赖 ORM）。

我们的应用层与基础设施层中间隔了一层"小领域对象"——为何这么做？

- 业务代码（``services``）以 ``UserSnapshot`` 而非 ``User`` ORM 模型为主语，
  避免在 service 里持有未关闭的 SQLAlchemy session 引用。
- ``UserSnapshot`` 也是 :class:`SessionData` 与 RBAC 决策的单一信息源——把
  从 Redis Session 拿到的字段绑成一个不可变值对象。
"""

from app.domain.user_snapshot import UserSnapshot

__all__ = ["UserSnapshot"]
