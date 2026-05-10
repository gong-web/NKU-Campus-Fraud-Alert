/**
 * 后端 API 类型定义（手工维护；将来通过 openapi-typescript-codegen 自动生成）。
 */

export interface WhoAmI {
  user_id: number;
  cas_account: string;
  real_name: string;
  role_id: number;
  role_code: "STUDENT" | "REVIEWER" | "SYS_ADMIN";
  department_id: number;
  permissions: string[];
  session_expires_in_seconds: number;
}

export interface PaginationOut<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface UserOut {
  user_id: number;
  cas_account: string;
  real_name: string;
  department_id: number;
  role_id: number;
  status: number;
  created_at?: string | null;
  last_login_at?: string | null;
}

export interface UserCreateIn {
  cas_account: string;
  real_name: string;
  department_id: number;
  role_id: number;
  email?: string | undefined;
  phone?: string | undefined;
}

export interface UserUpdateIn {
  role_id?: number;
  status?: number;
  reason?: string;
}

export interface AuditLogOut {
  log_id: number;
  operator_id: number;
  operation_type: string;
  object_type: string;
  object_id: string;
  source_ip: string;
  trace_id?: string | null;
  operated_at: string;
  before_state?: Record<string, unknown> | null;
  after_state?: Record<string, unknown> | null;
}

export interface JudicialDecryptRequestIn {
  report_id: number;
  judicial_doc_no: string;
  reason: string;
  related_case_no?: string | undefined;
}

export interface JudicialDecryptRequestOut {
  decrypt_log_id: number;
  expires_at: string;
  window_seconds: number;
}

export interface JudicialDecryptOut {
  report_id: number;
  user_id: number;
  real_name: string;
  cas_account: string;
  watermark_text: string;
  expires_at: string;
}
