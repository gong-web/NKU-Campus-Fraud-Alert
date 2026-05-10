# 平台权限码清单

> 任何 PR 加权限码前**必须**先在本文件登记。源码常量：`backend/app/services/permissions.py`。

格式：`<resource>:<action>`。

---

## 用户域（UC-10）

| 权限码                | 说明                       | 默认分配  |
| --------------------- | -------------------------- | --------- |
| `user:create`         | 创建账号                   | SYS_ADMIN |
| `user:read`           | 读取账号列表 / 详情        | SYS_ADMIN |
| `user:update`         | 更新账号（角色 / 状态）    | SYS_ADMIN |
| `user:disable`        | 停用账号                   | SYS_ADMIN |
| `user:batch_import`   | CSV 批量导入新生           | SYS_ADMIN |

## 审计 / 司法协助

| 权限码                       | 说明                   | 默认分配  |
| ---------------------------- | ---------------------- | --------- |
| `audit:read`                 | 查看审计日志           | SYS_ADMIN |
| `audit:export`               | 导出审计日志（也写审计）| SYS_ADMIN |
| `judicial:request_decrypt`   | 发起匿名身份解密申请   | SYS_ADMIN |

## 系统配置

| 权限码                  | 说明           | 默认分配  |
| ----------------------- | -------------- | --------- |
| `system_config:read`    | 读取系统参数   | SYS_ADMIN |
| `system_config:update`  | 更新系统参数   | SYS_ADMIN |

## 上报 / 审核（UC-01 / UC-02 / UC-06）

| 权限码                       | 说明                     | 默认分配                |
| ---------------------------- | ------------------------ | ----------------------- |
| `report:create`              | 提交事件                 | STUDENT                 |
| `report:read_own`            | 查看本人上报             | STUDENT                 |
| `report:read_all`            | 查看所有事件（含敏感）   | REVIEWER                |
| `report:review`              | 审核 / 状态流转          | REVIEWER                |
| `report:view_evidence`       | 解密查看证据             | REVIEWER                |

## 预警（UC-03 / UC-07）

| 权限码                | 说明              | 默认分配             |
| --------------------- | ----------------- | -------------------- |
| `warning:read`        | 浏览公开预警      | STUDENT / REVIEWER   |
| `warning:publish`     | 发布预警          | REVIEWER             |
| `warning:append`      | 追加后续说明      | REVIEWER             |
| `warning:offline`     | 手动下线预警      | REVIEWER             |

## 知识库（UC-04 / UC-08）

| 权限码         | 说明              | 默认分配             |
| -------------- | ----------------- | -------------------- |
| `kb:read`      | 浏览知识库        | STUDENT / REVIEWER   |
| `kb:create`    | 新建条目（草稿）  | REVIEWER             |
| `kb:review`    | 校级审核条目      | REVIEWER（校级）     |
| `kb:offline`   | 下线条目          | REVIEWER             |

## 测验（UC-05 / UC-09）

| 权限码                | 说明              | 默认分配  |
| --------------------- | ----------------- | --------- |
| `quiz:take`           | 参加测验          | STUDENT   |
| `quiz:bank_manage`    | 维护题库          | REVIEWER  |
| `quiz:assign`         | 发起指定测验      | REVIEWER  |
