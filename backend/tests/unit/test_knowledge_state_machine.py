"""单元：知识库状态机合法/非法转换矩阵测试（不上 client）。

直接使用 :data:`KnowledgeEntryStatus.TRANSITIONS` 与 service 层私有函数
``_ensure_can_transition``，覆盖：

- 合法路径：None→DRAFT, DRAFT→PENDING, PENDING→PUBLISHED, PUBLISHED→OFFLINE,
  PENDING→DRAFT (REJECT), OFFLINE→DRAFT (复活), DRAFT→OFFLINE, PENDING→OFFLINE
- 非法路径：每条都 assert raises :class:`KnowledgeIllegalTransition`
"""

from __future__ import annotations

import pytest

from app.exceptions import KnowledgeIllegalTransition
from app.infra.db.models.knowledge_entry import KnowledgeEntryStatus
from app.services.knowledge_entry_service import _ensure_can_transition

pytestmark = pytest.mark.unit


# ── 合法转换 ───────────────────────────────────────────────────────


LEGAL_TRANSITIONS: list[tuple[str | None, str]] = [
    (None, KnowledgeEntryStatus.DRAFT),
    (KnowledgeEntryStatus.DRAFT, KnowledgeEntryStatus.PENDING),
    (KnowledgeEntryStatus.DRAFT, KnowledgeEntryStatus.OFFLINE),
    (KnowledgeEntryStatus.PENDING, KnowledgeEntryStatus.PUBLISHED),
    (KnowledgeEntryStatus.PENDING, KnowledgeEntryStatus.DRAFT),
    (KnowledgeEntryStatus.PENDING, KnowledgeEntryStatus.OFFLINE),
    (KnowledgeEntryStatus.PUBLISHED, KnowledgeEntryStatus.OFFLINE),
    (KnowledgeEntryStatus.OFFLINE, KnowledgeEntryStatus.DRAFT),
]


@pytest.mark.parametrize(("from_status", "to_status"), LEGAL_TRANSITIONS)
def test_legal_transitions_pass(from_status: str | None, to_status: str) -> None:
    """合法转换不应抛异常。"""
    _ensure_can_transition(from_status, to_status)


# ── 非法转换 ───────────────────────────────────────────────────────


def _all_illegal_transitions() -> list[tuple[str | None, str]]:
    """枚举所有 (from, to) 中不在 ``TRANSITIONS[from]`` 内的对（含 self-loop）。"""
    all_states: list[str | None] = [None, *KnowledgeEntryStatus.ALL]
    illegal: list[tuple[str | None, str]] = []
    for src in all_states:
        allowed = KnowledgeEntryStatus.TRANSITIONS.get(src, frozenset())
        for dst in KnowledgeEntryStatus.ALL:
            if dst in allowed:
                continue
            illegal.append((src, dst))
    return illegal


ILLEGAL_TRANSITIONS = _all_illegal_transitions()


@pytest.mark.parametrize(("from_status", "to_status"), ILLEGAL_TRANSITIONS)
def test_illegal_transitions_raise(from_status: str | None, to_status: str) -> None:
    """每条非法路径都抛 KnowledgeIllegalTransition。"""
    with pytest.raises(KnowledgeIllegalTransition):
        _ensure_can_transition(from_status, to_status)


# ── 关键反例（人工列出，便于回归阅读）──────────────────────────────


CORE_ILLEGAL_PAIRS: list[tuple[str | None, str]] = [
    # 草稿不能直接发布
    (KnowledgeEntryStatus.DRAFT, KnowledgeEntryStatus.PUBLISHED),
    # 已发布不能直接回草稿
    (KnowledgeEntryStatus.PUBLISHED, KnowledgeEntryStatus.DRAFT),
    # 已发布不能再次审核
    (KnowledgeEntryStatus.PUBLISHED, KnowledgeEntryStatus.PENDING),
    # 已下线不能直接发布
    (KnowledgeEntryStatus.OFFLINE, KnowledgeEntryStatus.PUBLISHED),
    # 已下线不能进 PENDING
    (KnowledgeEntryStatus.OFFLINE, KnowledgeEntryStatus.PENDING),
    # PENDING 不能跳过 PUBLISHED 直奔 OFFLINE 之外的随机态
    # （这里覆盖：PENDING → PENDING 自环非法）
    (KnowledgeEntryStatus.PENDING, KnowledgeEntryStatus.PENDING),
]


@pytest.mark.parametrize(("from_status", "to_status"), CORE_ILLEGAL_PAIRS)
def test_core_illegal_pairs_raise(from_status: str, to_status: str) -> None:
    """业务关键反例：每条非法路径都抛 KnowledgeIllegalTransition。"""
    with pytest.raises(KnowledgeIllegalTransition):
        _ensure_can_transition(from_status, to_status)


def test_initial_state_only_draft() -> None:
    """新建条目（``from_status=None``）只能进入 DRAFT。"""
    _ensure_can_transition(None, KnowledgeEntryStatus.DRAFT)
    for invalid_target in (
        KnowledgeEntryStatus.PENDING,
        KnowledgeEntryStatus.PUBLISHED,
        KnowledgeEntryStatus.OFFLINE,
    ):
        with pytest.raises(KnowledgeIllegalTransition):
            _ensure_can_transition(None, invalid_target)
