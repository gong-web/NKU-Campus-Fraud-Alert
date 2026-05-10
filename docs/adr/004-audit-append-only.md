# ADR-004: 审计日志 数据库层 append-only

## 背景

PRD 5.4.3 强约束：审计日志"在数据库层面禁止 UPDATE / DELETE"。如何在 MySQL 8 上把这条约束做到无法绕开？

## 决策

**三道闸：**

1. **GRANT 层**：业务账号 `app_user` 仅有 `INSERT, SELECT` on `audit_logs`，无 `UPDATE / DELETE`。任何应用代码尝试 UPDATE / DELETE 都被 MySQL 拒绝（`Access denied`）。
2. **触发器层**：`trg_audit_logs_no_update` / `trg_audit_logs_no_delete` 在 BEFORE UPDATE / DELETE 上 `SIGNAL SQLSTATE '45000'` 兜底，即使 root 误操作也会被拒（除非显式 `DROP TRIGGER`）。
3. **链式哈希层（可选增强）**：`prev_hash || canonical_payload → this_hash`。`scripts/verify_audit_chain.py` 离线校验，篡改可被检测。

## 后果

**好处**

- 任何角色（哪怕是组员开发期手抖直接 UPDATE）都失败；合规可演示。
- 哈希链让"事后回放被篡改"也能被检测。

**代价**

- 任何 schema 变更（如加列）需要 root 在维护窗口操作；alembic 迁移在 CI 中用 root 跑。
- 复合 PK `(log_id, operated_at)` 是分区表的副作用，外键引用 `audit_log_id` 时需要应用层维持完整性（`AnonymousDecryptLog.audit_log_id` 已注释说明）。

## 替代方案

| 方案                | 否决原因                                  |
| ------------------- | ----------------------------------------- |
| 仅靠应用层"不写 update" | 任何 Bug 都会破坏铁律，无下限保障。       |
| WORM 文件 / 区块链  | 复杂度过高，且课程项目无对接资源。        |
| 仅 GRANT 不加触发器 | root / DBA 可能误操作；触发器多一道保险。 |
