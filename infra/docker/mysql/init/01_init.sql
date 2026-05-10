-- ──────────────────────────────────────────────────────────────────
-- MySQL 初始化（容器首次启动时由官方镜像自动执行）
--
-- 1. 创建 anti_fraud 数据库
-- 2. 字符集 utf8mb4，排序规则 utf8mb4_0900_ai_ci（PRD 第 6.1.2 节）
-- 3. SQL_MODE 严格模式
--
-- 注意：用户与权限授予在 02_grants.sql 处理。
-- ──────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS anti_fraud
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
