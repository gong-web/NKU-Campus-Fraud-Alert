"""数据访问层。

子模块：

- :mod:`app.infra.db.base`     — Declarative 基类 + 通用类型 / 字段
- :mod:`app.infra.db.session`  — async engine + session factory + Unit-of-Work
- :mod:`app.infra.db.types`    — 自定义 TypeDecorator（``EncryptedBinary``）
- :mod:`app.infra.db.models.*` — 一张表一个模块（按业务域分包）
"""
