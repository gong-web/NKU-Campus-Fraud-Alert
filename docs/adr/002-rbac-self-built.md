# ADR-002: RBAC 自研，不引 Casbin

## 背景

PRD 4.3.2 要求 RBAC 严格按权限矩阵执行；越权访问需"在服务端接口层拦截"。备选方案是引入 [Casbin](https://casbin.org)。

## 决策

**自研 RBAC**：`role -> {permission_code}` 的映射表 + Redis 缓存 + FastAPI Dependency 注入。

## 后果

**好处**

- 实现极朴素：3 个 Dependency（`require_role` / `require_permission` / `require_self_or_role`），团队 5 分钟看懂。
- 权限码集合在源码里枚举（`services/permissions.py`），mypy 帮你检查拼错。
- 不引入新依赖，CI 时长 / 镜像体积 / 学习成本都为 0 增量。

**代价**

- 不支持 Casbin 那种基于策略表达式的复杂场景（如"教师在自己院系内可读、跨院系不可读"）。本平台 PRD 范围内"自己 or 角色"已经够用。
- 自研意味着没有现成审计 / 可视化界面，但我们已经写了 `/sys/users` + `/sys/audit`，已覆盖业务需要。

## 替代方案

| 方案     | 否决原因                                                       |
| -------- | -------------------------------------------------------------- |
| Casbin   | 表达力强但 over-kill；ABAC / ReBAC 我们用不上。                |
| Oso      | 商业云倾斜，离线版功能裁剪。                                   |
| pure-Spring 风装饰器 | 与 FastAPI 的 Dependency 思路冲突。                |
