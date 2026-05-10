# Anti-Fraud Backend

> FastAPI 服务，承担登录、账号权限、审计、上报、审核、预警、知识库、测验等全部业务接口。

## 目录结构

```
backend/
  app/
    api/                # HTTP 入口层 (controller)，只做协议转换
      v1/               # 版本化路由
        auth.py
        users.py
        audit.py
        judicial.py
        _examples.py    # 给团队 4 人照抄的最小可工作示例
      deps.py           # 依赖注入：get_current_user / require_role / ...
      errors.py         # 全局异常处理器
    core/               # 框架级能力（配置、日志、安全、ID）
      config.py
      logging.py
      security.py
      snowflake.py
      kms.py
    domain/             # 纯领域对象，不依赖 ORM
      user.py / role.py / permission.py / audit_log.py / session.py
    infra/              # 基础设施实现
      db/               # SQLAlchemy 模型 + session
      cas/              # CAS Provider 抽象 + Real + Mock
      cache/            # Redis 客户端封装
      repositories/     # 仓储接口与实现
    services/           # 业务服务（用例编排）
      auth_service.py
      user_service.py
      audit_service.py     # ★ 审计 SDK（团队人均日调用 N 次）
      judicial_service.py
    schemas/            # Pydantic DTO
    exceptions.py       # AppException 体系
    main.py             # FastAPI app 工厂
  alembic/              # 数据库迁移
  tests/                # unit / integration / e2e
```

完整理由见 [`../docs/architecture.md`](../docs/architecture.md)。

## 本地开发

详见 [`../docs/getting-started.md`](../docs/getting-started.md)。

## 添加一个新接口（5 步）

详见 [`../docs/api-guide.md`](../docs/api-guide.md)。

## 依赖管理

使用 [`uv`](https://github.com/astral-sh/uv)：

```bash
uv sync                       # 安装全部依赖
uv add <pkg>                  # 加运行时依赖
uv add --group dev <pkg>      # 加开发依赖
uv add --group test <pkg>     # 加测试依赖
```

> 不使用 `pip install`，避免 `requirements.txt` 与 `pyproject.toml` 版本漂移。

## 测试

```bash
pytest                         # 全部
pytest tests/unit -ra          # 仅单元
pytest -m integration          # 仅集成
pytest --cov=app --cov-report=term-missing
```

覆盖率门槛：整体 ≥ 80%，关键模块（auth / audit）≥ 95%。
