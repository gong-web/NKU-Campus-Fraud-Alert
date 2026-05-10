"""CAS 单点登录 Provider。

抽象接口
--------
:class:`AuthProvider` —— 任何具体 CAS 接入方式都实现这两个方法：

- ``validate_ticket(ticket: str) -> CASUserInfo``
- ``logout_url(service: str) -> str``

实现
----
- :class:`RealCASProvider`  —— 真接学校 CAS 3.0
- :class:`MockCASProvider`  —— 本地开发用，输入学号即视为认证成功

通过 ``Settings.auth_provider`` 切换。生产环境强制 real。
"""

from app.infra.cas.base import AuthProvider, CASUserInfo
from app.infra.cas.factory import build_auth_provider, get_auth_provider
from app.infra.cas.mock import MockCASProvider
from app.infra.cas.real import RealCASProvider

__all__ = [
    "AuthProvider",
    "CASUserInfo",
    "MockCASProvider",
    "RealCASProvider",
    "build_auth_provider",
    "get_auth_provider",
]
