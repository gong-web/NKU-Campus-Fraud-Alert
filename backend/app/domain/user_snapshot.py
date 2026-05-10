"""``UserSnapshot``：当前请求的"身份名片"。

由 :func:`app.api.deps.get_current_user` 注入，只读地传给 service 层。
service 不允许直接拿 ORM ``User`` 修改字段，必须经仓储。

这条边界让 controller / service 的代码片段与"数据库连接是否打开"完全解耦——
单元测试中可以直接 ``UserSnapshot(...)`` 造一个再调 service。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserSnapshot:
    """请求级用户视图（不可变）。"""

    user_id: int
    cas_account: str
    real_name: str
    role_id: int
    role_code: str
    department_id: int
    session_id: str
    source_ip: str
    user_agent: str

    @property
    def is_sysadmin(self) -> bool:
        return self.role_code == "SYS_ADMIN"

    @property
    def is_reviewer(self) -> bool:
        return self.role_code == "REVIEWER"

    @property
    def is_student(self) -> bool:
        return self.role_code == "STUDENT"
