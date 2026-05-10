# ADR-008: Monorepo（不拆 backend / frontend 仓）

## 背景

`backend/` 与 `frontend/` 是否独立成两个 git 仓？

## 决策

**单仓多包（monorepo）**：顶层 `anti-fraud-platform/` 含 `backend/` `frontend/` `infra/` `docs/` `scripts/` `.github/`。

## 后果

**好处**

- 一次 commit 跨前后端原子提交（schema 改动 + 前端类型同步）。
- CI 一份；CODEOWNERS 一份；PR 模板一份；新人 1 次 clone。
- OpenAPI → 前端 types 自动生成 / diff 检查在同仓内可做。

**代价**

- 仓库尺寸略大；CI 缓存需分别打 key（已用 `cache-dependency-path` 区分）。
- backend / frontend 的依赖更新会撞上对方的 lock 文件；commitlint scope 区分即可。

## 替代方案

| 方案       | 否决原因                                                       |
| ---------- | -------------------------------------------------------------- |
| 双仓库     | 跨端联调时需要两套 PR；约定漂移；与"团队整体出活"目标相悖。       |
| 子模块     | 子模块更新链条长，新人易踩坑；`git submodule update` 噩梦。      |
