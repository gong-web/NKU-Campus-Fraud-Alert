-- Apply after `alembic upgrade head`.
-- MySQL official image creates app_user with broad privileges on the database;
-- once tables exist, narrow it to least privilege.

USE anti_fraud;

-- ===== app_user: business application =====
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'app_user'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.users TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.departments TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.roles TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.permissions TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.role_permissions TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.sessions TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.notifications TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.system_configs TO 'app_user'@'%';

-- Audit logs are append-only at DB permission level.
GRANT SELECT, INSERT
  ON anti_fraud.audit_logs TO 'app_user'@'%';

-- App can create decrypt request logs, but cannot read identity mappings.
GRANT INSERT
  ON anti_fraud.anonymous_decrypt_logs TO 'app_user'@'%';

-- ===== decrypt_user: judicial assistance only =====
CREATE USER IF NOT EXISTS 'decrypt_user'@'%' IDENTIFIED BY 'decryptpassword';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'decrypt_user'@'%';

GRANT SELECT
  ON anti_fraud.anonymous_mappings TO 'decrypt_user'@'%';
GRANT SELECT
  ON anti_fraud.anonymous_decrypt_logs TO 'decrypt_user'@'%';
GRANT INSERT
  ON anti_fraud.audit_logs TO 'decrypt_user'@'%';
GRANT SELECT
  ON anti_fraud.users TO 'decrypt_user'@'%';

-- Defense in depth: audit_logs is append-only even for accounts that
-- accidentally receive UPDATE/DELETE later.
DROP TRIGGER IF EXISTS trg_audit_logs_no_update;
DROP TRIGGER IF EXISTS trg_audit_logs_no_delete;

DELIMITER $$

CREATE TRIGGER trg_audit_logs_no_update BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'audit_logs is append-only';
END$$

CREATE TRIGGER trg_audit_logs_no_delete BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'audit_logs is append-only';
END$$

DELIMITER ;

FLUSH PRIVILEGES;
