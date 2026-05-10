# 工程规约（4 人照抄即可）

> 这一份文档的目的是：组员**不必思考"怎么命名 / 怎么放"**——一律照抄。

---

## 1. 命名

### Python

| 对象     | 规则                                  | 例子                              |
| -------- | ------------------------------------- | --------------------------------- |
| 模块     | 小写下划线，名词                      | `user_service.py`，**不**写 `do_user.py` |
| 类       | 大驼峰；接口/抽象带 `ABC`/纯抽象基类  | `UserRepositoryABC`               |
| 实现类   | 加技术后缀                            | `UserRepositorySQLAlchemy`        |
| 函数     | 动词开头                              | `create_user`，**不**写 `user_create` |
| 私有     | `_` 前缀                              | `_compute_hash`                   |
| 常量     | 全大写下划线                          | `SESSION_TTL_SECONDS`             |
| Pydantic | `XxxIn` / `XxxOut` / `XxxFilter`      | `UserCreateIn`、`UserOut`         |

### 数据库

| 对象     | 规则                              | 例子                  |
| -------- | --------------------------------- | --------------------- |
| 表       | 复数名词（snake_case）            | `users`、`audit_logs` |
| 主键     | `<entity>_id`                     | `user_id`             |
| 外键     | 同上 + 指向表                     | `department_id`       |
| 时间字段 | `_at` 后缀                        | `created_at`          |
| 布尔字段 | `is_` 前缀                        | `is_revoked`          |
| 索引     | `idx_<table>_<col1>_<col2>`       | `idx_user_dept_role`  |

### HTTP / API

- 路径：`/api/v1/<复数资源>`，**kebab-case**：`/api/v1/audit-logs`，**不**写 `/auditLogs` 或 `/audit_logs`。
- HTTP 方法语义：`GET` 只读、`POST` 创建、`PUT` 全量、`PATCH` 部分、`DELETE` 删除（本平台几乎不用）。
- 分页响应：`{ items, total, page, size }`，**不**自定义。
- 时间字段：ISO 8601 with timezone（`2026-05-08T14:30:00+08:00`），**不**写 `2026/5/8 14:30`。

### Git / 分支

- 分支名：`feature/<姓名缩写>-<UC编号>-<简述>`，例：`feature/yxq-uc10-csv-import`。
- Commit：[Conventional Commits](https://www.conventionalcommits.org/)，commitlint 强制。

---

## 2. 错误码

完整字典见 [`error-codes.md`](error-codes.md)。要点：

- 全平台**只能**返回 `{ code, message, data, trace_id }` 这一种格式。
- 写新错误前**必须**先在字典里登记。
- 错误码段位：`1xxxx` 通用 / `2xxxx` 用户 / `3xxxx` 上报 / `4xxxx` 预警 / `5xxxx` 教育 / `6xxxx` 审计 / `9xxxx` 外部依赖。

---

## 3. 日志

- 全平台**只能**通过 `app.core.logging.get_logger(__name__)` 获取 logger。
- **禁止 `print`、禁止 `logging.info("xxx" + variable)`、禁止 f-string 拼接 logger.info。**

✅ 正确：

```python
logger.info("user_login", user_id=u.id, source_ip=ip)
```

❌ 错误：

```python
logger.info(f"user {u.id} login from {ip}")
```

---

## 4. 异常

- Controller 不允许抛 `HTTPException`；改抛 `app.exceptions.AppException` 子类。
- Service 抛业务异常；不要在 service 里 catch 然后又 `raise HTTPException`。
- 已知失败必须显式分类（如 CAS 五种失败），**禁止** `except Exception:` 然后吞掉。

---

## 5. 测试

- 任何 PR 必带至少一条新测试。
- 公共 API 至少 1 个集成测试；service 至少 1 个单元测试。
- 命名：`test_<模块>_<行为>.py`，函数 `test_<expected_behavior>`。
- fixture：用 `tests/conftest.py` 里现成的；不在测试文件里自创 DB 连接 / Redis。

---

## 6. 提交清单（自查）

- [ ] 命名 / 错误码 / 日志符合本文件
- [ ] 路由接 `Depends(require_*)`，**不**写 `if user.role == ...`
- [ ] L2/L3 操作走 `audit.write()`
- [ ] 无 `print`、无裸 `try/except: pass`
- [ ] 无硬编码 secret
- [ ] 测试 + 文档同步更新
