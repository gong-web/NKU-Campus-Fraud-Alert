"""业务服务层（Service Layer）。

特点
----
- 用例编排：把多个仓储 + Redis + 审计 + 通知粘合成一个完整业务动作。
- 不直接持有 SQLAlchemy session；通过 ``app.infra.db.session.uow()`` 显式开
  事务。
- 不直接抛 ``HTTPException``，统一抛 :mod:`app.exceptions` 中的 AppException
  子类。

模块
----
- :mod:`app.services.audit_service`     — **审计 SDK**（团队所有人调用）
- :mod:`app.services.auth_service`      — CAS 登录 / 登出 / 会话续期
- :mod:`app.services.user_service`      — 账号 CRUD / 角色变更 / 批量导入
- :mod:`app.services.judicial_service`  — UC-10 备选 A2 司法协助查询
- :mod:`app.services.permissions`       — 平台所有权限码常量
"""
