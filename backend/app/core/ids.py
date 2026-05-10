"""业务 ID 工具（trace_id、case_no 等）。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

# PRD 5.4.3：FraudReport.case_no 必须匹配 ``^\d{4}-[A-Z0-9]{2,8}-\d{6}$``。
# 例如 ``2026-CS-000123``。
_CASE_NO_FMT = "{year:04d}-{dept_code}-{seq:06d}"


def new_trace_id() -> str:
    """生成请求级别 trace_id。"""
    return uuid.uuid4().hex


def make_case_no(*, dept_code: str, sequence: int, now: datetime | None = None) -> str:
    """根据"年份-院系代码-流水号"生成案件编号。

    ``dept_code`` 必须是 2-8 位大写字母 / 数字（PRD 5.4.3 正则）；
    ``sequence`` 由数据库 / 雪花派生，本函数不负责唯一性。
    """
    now = now or datetime.now(tz=UTC)
    if not dept_code or not dept_code.isascii() or not dept_code.replace("_", "").isalnum():
        raise ValueError(f"非法 dept_code: {dept_code!r}")
    if not 2 <= len(dept_code) <= 8:
        raise ValueError(f"dept_code 长度必须 2~8: {dept_code!r}")
    if not 0 <= sequence <= 999_999:
        raise ValueError(f"sequence 越界 0~999999: {sequence}")
    return _CASE_NO_FMT.format(year=now.year, dept_code=dept_code.upper(), seq=sequence)
