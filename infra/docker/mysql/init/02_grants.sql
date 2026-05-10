-- ──────────────────────────────────────────────────────────────────
-- 权限分离（PRD 5.5.3 + 第 4.1 节"审计不可变"）
--
-- 三个数据库账号：
--
--   1. root          —— 仅运维使用；docker-compose 启动时由 ENV 注入
--   2. app_user      —— 业务应用唯一可用账号
--                         · 对绝大多数表 SELECT/INSERT/UPDATE/DELETE
--                         · 对 audit_logs    仅 SELECT/INSERT（不可改 / 不可删）
--                         · 对 anonymous_mappings、anonymous_decrypt_logs
--                                            **零** 权限
--
--   3. decrypt_user  —— 仅司法协助查询专用
--                         · 对 anonymous_mappings、anonymous_decrypt_logs SELECT
--                         · 对 audit_logs   仅 INSERT（写解密留痕）
--                         · 对其它表 **零** 权限
--
-- 这一分离保证：即使应用代码因 Bug 试图越权访问匿名身份表，
-- MySQL 在数据库层就拒绝；ORM 配错 / 业务越界 / 注入攻击都拦截在这一层。
-- ──────────────────────────────────────────────────────────────────

USE anti_fraud;

-- Table-level grants cannot run during MySQL image initialization because
-- Alembic creates the tables later. This init script only creates the
-- dedicated decrypt account; run ../post_migration/01_grants.sql after
-- `alembic upgrade head` to apply least-privilege table grants.
CREATE USER IF NOT EXISTS 'decrypt_user'@'%' IDENTIFIED BY 'decryptpassword';

FLUSH PRIVILEGES;
