import type { PaginationOut } from "./api";

export interface FraudType {
  type_id: number;
  type_code: string;
  type_name: string;
  description: string | null;
  sort_order: number;
}

export interface ReportCreateIn {
  title: string;
  description: string;
  fraud_type_id: number;
  incident_date: string;
  amount?: number | null;
  fraud_method?: string | null;
  is_anonymous: boolean;
  contact_way?: string | null;
}

export interface ReportOut {
  case_id: string;
  case_no: string;
  title: string;
  status: string;
  fraud_type_id: number;
  fraud_type_name: string | null;
  incident_date: string;
  amount: number | null;
  is_anonymous: boolean;
  dept_code: string;
  created_at: string;
  updated_at: string;
}

export interface StatusHistoryOut {
  history_id: string;
  from_status: string | null;
  to_status: string;
  operator_id: string;
  note: string | null;
  created_at: string;
}

export interface EvidenceFileOut {
  file_id: string;
  original_name: string;
  file_size: number;
  mime_type: string;
  uploaded_at: string;
}

export interface ReportDetailOut extends ReportOut {
  description: string;
  fraud_method: string | null;
  contact_way: string | null;
  review_note: string | null;
  reviewed_at: string | null;
  history: StatusHistoryOut[];
  evidence_count: number;
}

export interface DraftSaveIn {
  title?: string | null;
  description?: string | null;
  fraud_type_id?: number | null;
  incident_date?: string | null;
  amount?: number | null;
  fraud_method?: string | null;
  is_anonymous: boolean;
  contact_way?: string | null;
}

export interface DraftOut {
  draft_id: string;
  title: string | null;
  description: string | null;
  fraud_type_id: number | null;
  incident_date: string | null;
  amount: number | null;
  fraud_method: string | null;
  is_anonymous: boolean;
  contact_way: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string;
  evidence_count: number;
  evidence_list: EvidenceFileOut[];
}

export interface AdminReportListItem {
  case_id: string;
  case_no: string;
  fraud_type_id: number;
  fraud_type_name: string | null;
  title: string;
  amount: number | null;
  status: string;
  created_at: string;
  is_anonymous: boolean;
  evidence_count: number;
}

export interface ReviewerSummary {
  user_id: string;
  real_name: string;
}

export interface ReporterSummary {
  user_id: string;
  real_name: string;
  cas_account: string;
  department_id: number;
}

export interface AdminReportDetail {
  case_id: string;
  case_no: string;
  title: string;
  description: string;
  fraud_type_id: number;
  fraud_type_name: string | null;
  incident_date: string;
  amount: number | null;
  fraud_method: string | null;
  contact_way: string | null;
  created_at: string;
  updated_at: string;
  status: string;
  is_anonymous: boolean;
  dept_code: string;
  review_note: string | null;
  reviewed_at: string | null;
  reviewer: ReviewerSummary | null;
  reporter: ReporterSummary | null;
  evidence_list: EvidenceFileOut[];
  history: StatusHistoryOut[];
}

export interface AdminReportListParams {
  status?: string[];
  fraud_type_id?: number;
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  keyword?: string;
  page?: number;
  size?: number;
  sort?: "created_at_desc" | "amount_desc";
}

export interface ResolveReportIn {
  desensitized_summary: string;
  identification_points: string;
  prevention_advice: string;
  internal_remark?: string | null;
}

export interface RejectReportIn {
  reason: string;
  internal_remark?: string | null;
}

export interface TransferReportIn {
  transfer_note: string;
  internal_remark?: string | null;
}

export interface ContactInfoOut {
  phone: string | null;
  email: string | null;
}

export interface AnonymousDecryptIn {
  reason: string;
  approver_id?: string | null;
}

export interface AnonymousDecryptOut {
  case_id: string;
  user_id: string;
  real_name: string;
  cas_account: string;
  phone: string | null;
  email: string | null;
  expires_at: string;
}

export interface DashboardTrendPoint {
  date: string;
  submitted: number;
  handled: number;
}

export interface RecentActionOut {
  case_id: string;
  case_no: string;
  to_status: string;
  note: string | null;
  created_at: string;
}

export interface DashboardSummaryOut {
  pending_count: number;
  reviewing_count: number;
  today_handled: number;
  today_rejected: number;
  today_reported: number;
  trend_7days: DashboardTrendPoint[];
  my_recent_actions: RecentActionOut[];
}

export type ReportPagination = PaginationOut<ReportOut>;
export type AdminReportPagination = PaginationOut<AdminReportListItem>;
