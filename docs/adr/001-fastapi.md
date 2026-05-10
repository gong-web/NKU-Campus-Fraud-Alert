# ADR-001: 后端选 FastAPI（不选 Django / Flask）

## 背景

PRD 第 6.1.1 节已经把后端语言固定到 Python 3.11+。我们仍需在以下三种主流框架里选一种：Django、Flask、FastAPI。

## 决策

**采用 FastAPI 0.110+**。配套：SQLAlchemy 2.x async + Alembic + Pydantic v2 + Uvicorn + Gunicorn。

## 后果

**好处**

- Pydantic v2 同时承担入参校验 + 出参 schema + OpenAPI 文档生成 — 单一真相源。
- 原生 async/await，与 PRD 性能目标（首屏 ≤ 3s、上报 ≤ 5s）匹配。
- `Depends(...)` 是依赖注入模型，与"权限装饰器"思路天然契合。
- `/docs` 自动生成 OpenAPI 满足 PRD 4.6.2 接口可读文档要求。

**代价**

- 不像 Django 自带 ORM / Admin / 表单 / 用户系统；要自己组合 SQLAlchemy + Alembic + Element Plus 表单。
- 异步生态比同步成熟度低（`aiomysql` < `pymysql`）；少数库需 `asyncio.to_thread` 绕开。

## 替代方案

| 方案    | 否决原因                                                                 |
| ------- | ------------------------------------------------------------------------ |
| Django  | "电池"过多但学习曲线陡；与 PRD 推荐的 RBAC + RESTful + 自定义鉴权契合差。 |
| Flask   | 轻但要自拼校验 / DI / OpenAPI；最终复杂度高于 FastAPI。                  |
| Litestar | 接口优雅，但生态 / 社区资料相比 FastAPI 仍小一个量级。                  |
