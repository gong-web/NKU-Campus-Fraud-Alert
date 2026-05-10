"""框架级能力：配置、日志、安全、ID 生成、KMS。

本包是平台地基，所有业务代码都通过它访问以下能力：

- :mod:`app.core.config`     — 类型化配置（Pydantic Settings v2）
- :mod:`app.core.logging`    — 结构化日志（structlog 全平台唯一入口）
- :mod:`app.core.security`   — AES-256-GCM 字段加密、签名 / 验签
- :mod:`app.core.snowflake`  — 雪花 ID 生成器
- :mod:`app.core.kms`        — 密钥管理服务抽象（Local / Vault / AWS）
- :mod:`app.core.ids`        — UUID / case_no 等业务 ID 工具
"""
