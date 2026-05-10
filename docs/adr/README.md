# Architecture Decision Records (ADR)

每篇 ADR 4 段：**背景 / 决策 / 后果 / 替代方案**。

| ID  | 标题                                  |
| --- | ------------------------------------- |
| 001 | 后端选 FastAPI（不选 Django / Flask） |
| 002 | RBAC 自研，不引 Casbin                |
| 003 | 不引入 GraphQL                        |
| 004 | 审计日志数据库层 append-only          |
| 005 | 后端 async 默认                       |
| 006 | 提供 Mock CAS Provider                |
| 007 | 主键差异化策略（雪花 / 自增 / UUID）  |
| 008 | Monorepo（不拆 backend / frontend 仓）|

---

## 模板

```markdown
# ADR-NNN: <一句话决策>

## 背景
（为什么需要做这个决定？）

## 决策
（最终选择什么？）

## 后果
（带来的好处与代价）

## 替代方案
（考虑过但被否决的方案 + 否决原因）
```
