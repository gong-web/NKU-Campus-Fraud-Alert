"""基础设施实现层（基础设施实现层）。

本层包含与具体外部组件耦合的实现：

- :mod:`app.infra.db`           — SQLAlchemy 模型 + session
- :mod:`app.infra.cas`          — CAS Provider（Real / Mock）
- :mod:`app.infra.cache`        — Redis 客户端封装
- :mod:`app.infra.repositories` — 仓储模式实现

业务代码（:mod:`app.services` / :mod:`app.api`）只通过仓储接口调用本层，
不直接 import SQLAlchemy 的 ``Session`` —— 见 ``docs/architecture.md``。
"""
