# ADR-006: 提供 Mock CAS Provider

## 背景

学校 CAS 系统:1) 不一定能在课程一年内开放接入；2) 即使开放，也不允许大家本地连真 CAS 跑测试。组员开发体验首要：拿到仓库就能跑通登录。

## 决策

**抽象 `AuthProvider` 接口，提供 `RealCASProvider` + `MockCASProvider` 两个实现，通过 `Settings.auth_provider` 切换。**

- `MockCASProvider`：前端登录页输入学号即视为登录成功，返回固定 mock 用户。
- `RealCASProvider`：CAS 3.0 协议（`/p3/serviceValidate` + XML），用 defusedxml 防 XXE。

## 后果

**好处**

- 组员 30 秒登录成功；本地开发与真 CAS 解耦。
- Real / Mock 共享同一套去重 / 白名单 / 审计逻辑，切换风险低。
- 测试可直接用 Mock，无须搭 CAS。

**代价**

- 必须保证生产环境强制 `AUTH_PROVIDER=real`（已在 `Settings._check_prod_invariants` 启动期校验）。
- 两个 Provider 的行为差异需要在文档里写清，否则可能"本地能跑生产挂"。

## 替代方案

| 方案                      | 否决原因                                |
| ------------------------- | --------------------------------------- |
| 强制接学校 CAS            | 阻塞所有人开发体验。                    |
| 用 Keycloak 自建 CAS      | 增加运维负担；与 PRD"对接学校"目标背离。|
| 在登录路径分支 `if dev: ...` | 污染主路径；难以 mypy 严校验。          |
