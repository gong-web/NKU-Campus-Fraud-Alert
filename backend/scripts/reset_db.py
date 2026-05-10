"""drop + create database（仅 dev / test 用）。

用法：``python -m scripts.reset_db``
"""

from __future__ import annotations

import asyncio
import sys
from urllib.parse import urlparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def reset() -> None:
    settings = get_settings()
    if settings.app_env == "prod":
        raise SystemExit("拒绝在生产环境执行 reset_db")

    parsed = urlparse(settings.database_url)
    db_name = parsed.path.lstrip("/").split("?", 1)[0]
    if not db_name:
        raise SystemExit("DATABASE_URL 必须包含数据库名")

    server_url = settings.database_url.replace(f"/{db_name}", "/", 1)
    engine = create_async_engine(server_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        logger.warning("dropping_database", db=db_name)
        await conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
        logger.info("creating_database", db=db_name)
        await conn.execute(
            text(f"CREATE DATABASE `{db_name}` " "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
        )
    await engine.dispose()
    logger.info("reset_done", db=db_name)


def _main() -> None:
    configure_logging(level="INFO")
    asyncio.run(reset())


if __name__ == "__main__":
    sys.exit(_main())
