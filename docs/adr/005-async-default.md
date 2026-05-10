# ADR-005: 后端 async 默认

## 背景

FastAPI 同时支持 sync 与 async；混用容易造成"async 路径里偶尔阻塞 IO"事故。

## 决策

**所有业务接口默认 `async`**。数据库用 SQLAlchemy 2.x async + `aiomysql`；Redis 用 `redis.asyncio`；HTTP 用 `httpx.AsyncClient`。

## 后果

**好处**

- 性能：单进程多协程吃满 CPU 之前不必扩 worker。
- 一致：组员不必思考"该用 sync 还是 async"。

**代价**

- 任何同步阻塞 IO（如 `requests.get`、`time.sleep`）都会阻断事件循环；必须用 `asyncio.to_thread` 包裹。
- 部分库（如 SMTP / 旧版 Redis 客户端）只有 sync，仍需 `to_thread`。
- 调试栈帧更深；新人理解曲线略陡，但 PR review 模板里强调一次足够。

## 替代方案

| 方案 | 否决原因                                        |
| ---- | ----------------------------------------------- |
| 全 sync | 性能不达标；与 SQLAlchemy 2.x async 主推方向相反。 |
| 混用 | 灾难——事故现场常见模式。                       |
