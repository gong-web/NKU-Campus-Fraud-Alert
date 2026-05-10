"""测试包。

测试金字塔（PRD 第 4 章可维护性 + 我们的工程基线）：

- ``tests/unit``        — 60%。无 IO，毫秒级，快。
- ``tests/integration`` — 30%。带 DB / Redis，每文件 ≤ 数秒。
- ``tests/e2e``         — 10%。冒烟级 only，5 分钟跑完。
"""
