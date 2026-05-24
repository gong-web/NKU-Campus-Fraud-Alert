-- Minimal demo quiz data (SCHOOL publisher only)
USE anti_fraud;
SET NAMES utf8mb4;

-- Assumes quiz tables are already truncated.

-- Quizzes
INSERT INTO quizzes (
  quiz_id, quiz_type, title, question_count, pass_score, status,
  created_by, deadline_at, target_scope, reminder_sent, publish_level,
  created_at, updated_at
) VALUES
(
  184285799850840064,
  'ASSIGNED',
  '【学校】全校反诈测验（演示）',
  10,
  60,
  'ACTIVE',
  184228404437061632,
  DATE_ADD(UTC_TIMESTAMP(), INTERVAL 7 DAY),
  JSON_OBJECT('type','ALL'),
  0,
  2,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
);

-- Quiz questions
INSERT INTO quiz_questions (quiz_id, question_id, sort_order) VALUES
  (184285799850840064, 184235258047238144, 1),
  (184285799850840064, 184228762810978304, 2),
  (184285799850840064, 184228404554502144, 3),
  (184285799850840064, 184228404550307840, 4),
  (184285799850840064, 184228404546113536, 5),
  (184285799850840064, 184228404541919233, 6),
  (184285799850840064, 184228404541919232, 7),
  (184285799850840064, 184228404533530625, 8),
  (184285799850840064, 184228404533530624, 9),
  (184285799850840064, 184228404529336320, 10);

-- Attempts
INSERT INTO quiz_attempts (
  attempt_id, quiz_id, student_id, status, score, correct_count, started_at, submitted_at
) VALUES
  -- student001 (dept=2)
  (184285799900000001, 184285799850840064, 184228404437061633, 'SUBMITTED', 80, 8, UTC_TIMESTAMP(), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 5 MINUTE)),
  -- student002 (dept=3)
  (184285799900000003, 184285799850840064, 184228404441255936, 'SUBMITTED', 50, 5, UTC_TIMESTAMP(), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 7 MINUTE));
