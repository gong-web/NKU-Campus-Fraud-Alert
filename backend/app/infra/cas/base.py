"""CAS Provider 接口与共享数据对象。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CASUserInfo:
    """CAS 校验通过后返回的用户基础实名信息。

    平台不依赖 CAS 提供的角色字段（CAS 通常没有），角色由本地 ``users`` 表
    决定；首次登录的合法师生默认为 ``Student``。
    """

    cas_account: str
    """学号 / 工号（与本地 ``User.cas_account`` 一致）"""

    real_name: str
    """学校实名"""

    department_code: str | None = None
    """CAS 返回的院系代码（可能没有；没有就用 ``UNKNOWN``）"""

    raw_attributes: dict[str, str] | None = None
    """完整原始属性（保留用于 debug，但不写入业务库）"""


class AuthProvider(ABC):
    """CAS Provider 抽象。

    Implementations
    ---------------
    - :class:`RealCASProvider` (CAS 3.0 over HTTPS)
    - :class:`MockCASProvider` (本地开发)
    """

    name: str

    @abstractmethod
    async def validate_ticket(self, ticket: str, *, service: str) -> CASUserInfo:
        """校验票据并返回用户实名信息。

        失败抛 :class:`app.exceptions.CASTicketInvalid` 等异常。
        """

    @abstractmethod
    def login_url(self, *, service: str) -> str:
        """生成 CAS ``/login?service=...`` 重定向 URL。"""

    @abstractmethod
    def logout_url(self, *, service: str | None = None) -> str:
        """生成 CAS ``/logout`` URL（含可选回跳）。"""

    @abstractmethod
    async def healthy(self) -> bool:
        """健康探针：连续 3 次 false 触发降级提示页（见 PRD 第 2.2 章）。"""
