"""HTTP 入口层。

只允许做 4 件事：

1. 协议转换（HTTP ↔ Pydantic ↔ service 调用）
2. 鉴权依赖注入（``deps.py``）
3. 异常翻译（``errors.py``）
4. 文档元数据（OpenAPI tags / responses）

**禁止**在本层写业务规则、直接 import SQLAlchemy ``Session`` 或 Redis。
"""
