/** 安全测验相关类型。ID 字段使用 string，避免大整数精度问题。 */

export type OptionLetter = "A" | "B" | "C" | "D";
export type QuizType = "RANDOM" | "ASSIGNED";
export type QuizStatus = "ACTIVE" | "CANCELLED" | "FINISHED";
export type ScopeType = "ALL" | "DEPT" | "USERS";
export type Difficulty = 1 | 2 | 3;
export type AttemptStatus = "IN_PROGRESS" | "SUBMITTED";

// ── 题库 ──────────────────────────────────────────────────────────
export interface QuestionAdmin {
  question_id: string;
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: OptionLetter;
  explanation: string | null;
  fraud_type_id: number | null;
  knowledge_entry_id: string | null;
  difficulty: Difficulty;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionCreateBody {
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: OptionLetter;
  explanation?: string | null;
  fraud_type_id?: number | null;
  knowledge_entry_id?: number | null;
  difficulty: Difficulty;
}

export interface QuestionUpdateBody extends Partial<QuestionCreateBody> {
  is_active?: boolean;
}

export interface QuestionListParams {
  keyword?: string;
  fraud_type_id?: number;
  difficulty?: Difficulty;
  is_active?: boolean;
  page?: number;
  size?: number;
}

// ── 测验 ──────────────────────────────────────────────────────────
export interface QuizListItem {
  quiz_id: string;
  quiz_type: QuizType;
  title: string;
  question_count: number;
  pass_score: number;
  status: QuizStatus;
  deadline_at: string | null;
  created_at: string;
  publish_level: 1 | 2;
  my_attempt_status?: AttemptStatus | null;
  my_score?: number | null;
}

export interface QuizDetail {
  quiz_id: string;
  quiz_type: QuizType;
  title: string;
  question_count: number;
  pass_score: number;
  status: QuizStatus;
  created_by: string;
  deadline_at: string | null;
  target_scope: { type: ScopeType; dept_ids?: number[]; user_ids?: number[] } | null;
  created_at: string;
}

export interface AssignedQuizCreateBody {
  title: string;
  question_ids: Array<string | number>;
  pass_score: number;
  deadline_at: string;
  scope_type: ScopeType;
  dept_ids?: number[] | null;
  user_ids?: number[] | null;
}

export interface QuizCancelBody {
  reason: string;
}

// ── 答题 ──────────────────────────────────────────────────────────
export interface StudentQuestion {
  question_id: string;
  sort_order: number;
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

export interface StartQuizOut {
  quiz_id: string;
  attempt_id: string;
  title: string;
  pass_score: number;
  question_count: number;
  questions: StudentQuestion[];
}

export interface SubmitAnswerItem {
  question_id: string | number;
  chosen_answer: OptionLetter | null;
}

export interface SubmitQuizBody {
  answers: SubmitAnswerItem[];
}

export interface QuestionResult {
  question_id: string;
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: OptionLetter;
  chosen_answer: OptionLetter | null;
  is_correct: boolean;
  explanation: string | null;
  knowledge_entry_id: string | null;
}

export interface SubmitQuizOut {
  quiz_id: string;
  attempt_id: string;
  score: number;
  pass_score: number;
  is_pass: boolean;
  correct_count: number;
  total_count: number;
  submitted_at: string;
  results: QuestionResult[];
}

export interface WrongQuestion {
  question_id: string;
  quiz_id: string;
  attempt_id: string;
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: OptionLetter;
  chosen_answer: OptionLetter | null;
  explanation: string | null;
  knowledge_entry_id: string | null;
  wrong_at: string;
}

export interface QuizHistoryItem {
  attempt_id: string;
  quiz_id: string;
  quiz_type: QuizType;
  quiz_title: string;
  pass_score: number;
  score: number;
  correct_count: number;
  total_count: number;
  is_pass: boolean;
  started_at: string;
  submitted_at: string;
}

// ── 报告 ──────────────────────────────────────────────────────────
export interface DepartmentCompletionItem {
  dept_id: number;
  dept_name: string;
  total_targets: number;
  submitted_count: number;
  completion_rate: number;
  pass_count: number;
  pass_rate: number;
  avg_score: number;
}

export interface QuizCompletionReport {
  quiz_id: string;
  title: string;
  status: QuizStatus;
  deadline_at: string | null;
  total_targets: number;
  submitted_count: number;
  completion_rate: number;
  pass_rate: number;
  avg_score: number;
  by_department: DepartmentCompletionItem[];
}
