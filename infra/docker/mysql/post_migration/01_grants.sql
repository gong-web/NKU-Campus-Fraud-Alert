-- Apply after `alembic upgrade head`.
-- MySQL official image creates app_user with broad privileges on the database;
-- once tables exist, narrow it to least privilege.
--
-- NOTE:
-- - Alembic needs to read/write `alembic_version`.
-- - If you run migrations using app_user, it also needs DDL privileges.

USE anti_fraud;

-- ===== app_user: business application =====
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'app_user'@'%';

-- Alembic version table (required for migrations)
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.alembic_version TO 'app_user'@'%';

-- Development convenience: allow app_user to run migrations (DDL)
GRANT CREATE, ALTER, INDEX, DROP
  ON anti_fraud.* TO 'app_user'@'%';

-- 0001_initial
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

-- 0002_yxq_reports: fraud_types / report_drafts / fraud_cases /
--                   evidence_files / case_status_histories / case_anonymous_reporters
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.fraud_types TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.report_drafts TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.fraud_cases TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.evidence_files TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.case_status_histories TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.case_anonymous_reporters TO 'app_user'@'%';

-- 0003_gzh_review: knowledge_drafts / aggregate_alert_logs
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.knowledge_drafts TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.aggregate_alert_logs TO 'app_user'@'%';

-- 0004_lht_warnings_kb: warning_notices / warning_targets /
--                        knowledge_entries / knowledge_entry_history
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.warning_notices TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.warning_targets TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.knowledge_entries TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.knowledge_entry_history TO 'app_user'@'%';

-- 0006_tsy_quiz: question_bank / quizzes / quiz_questions /
--                 quiz_attempts / quiz_attempt_answers
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.question_bank TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.quizzes TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.quiz_questions TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.quiz_attempts TO 'app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON anti_fraud.quiz_attempt_answers TO 'app_user'@'%';

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