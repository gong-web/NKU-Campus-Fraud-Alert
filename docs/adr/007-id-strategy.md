# ADR-007: 主键差异化策略

## 背景

PRD 5.4.1 明确：业务核心实体用雪花 ID，字典表用自增，会话用 UUID。

## 决策

| 实体类                                                   | 主键      | 理由                                                |
| -------------------------------------------------------- | --------- | --------------------------------------------------- |
| FraudReport / Evidence / KnowledgeEntry / AuditLog / Notification / User …| 雪花 ID（64 位）  | 时间有序、分布式无冲突、不暴露规模 |
| Department / Role / Permission / FraudType / SystemConfig | 自增 ID（INT） | 字典表低频写入，简单高效                |
| Session                                                  | UUID v4   | 不可预测，防会话固定                                |
| RolePermission / WarningTarget / WarningRead / QuizQuestion | 复合主键 | 多对多关联，天然防止重复                            |

## 后果

**好处**

- 雪花 ID 时间有序：``ORDER BY id`` 即时间序，省一个 ``created_at`` 索引。
- 雪花 ID 不暴露业务规模：攻击者不能通过 ``id+1`` 推断"系统有多少用户"。
- UUID v4 防会话固定攻击。

**代价**

- 雪花 ID 是 BIGINT，比 INT 多 4 字节；可接受。
- 多个 worker 时必须给每个 worker 不同 `worker_id`（已通过 `SNOWFLAKE_WORKER_ID` 注入）。

## 替代方案

| 方案       | 否决原因                                                       |
| ---------- | -------------------------------------------------------------- |
| 全 UUID    | 字符串主键 8 字节 → 16 字节，索引膨胀；无时间序列。              |
| 全自增     | 暴露业务规模；分布式分库分表时冲突。                            |
| ULID       | 与雪花类似但生态不足；雪花有现成工具。                          |
