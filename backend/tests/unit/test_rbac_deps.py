"""RBAC dependency 单元测试（角色限定、权限码、self_or_role）。"""

from __future__ import annotations

import pytest

from app.api.deps import _normalize


class TestNormalizeRoles:
    @pytest.mark.parametrize(
        "given,expected",
        [
            (("Student",), {"STUDENT"}),
            (("REVIEWER", "sysadmin"), {"REVIEWER", "SYS_ADMIN"}),
            (("Admin",), {"SYS_ADMIN"}),
            (("Student", "STUDENT"), {"STUDENT"}),
            (("Sys-Admin",), {"SYS_ADMIN"}),
        ],
    )
    def test_known(self, given: tuple[str, ...], expected: set[str]) -> None:
        assert _normalize(given) == frozenset(expected)

    def test_unknown(self) -> None:
        with pytest.raises(ValueError):
            _normalize(("Hacker",))
