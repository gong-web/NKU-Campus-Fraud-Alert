import http from "./http";

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
  incident_date: string; // YYYY-MM-DD
  amount?: number | null;
  fraud_method?: string | null;
  is_anonymous: boolean;
  contact_way?: string | null;
}

export interface ReportOut {
  case_id: number;
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
  history_id: number;
  from_status: string | null;
  to_status: string;
  operator_id: number;
  note: string | null;
  created_at: string;
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

export interface EvidenceFileOut {
  file_id: number;
  original_name: string;
  file_size: number;
  mime_type: string;
  uploaded_at: string;
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
  draft_id: number;
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
}

export interface PaginationOut<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const reportsApi = {
  async listFraudTypes(): Promise<FraudType[]> {
    const r = await http.get("/api/v1/fraud-types");
    return r.data;
  },

  async createReport(data: ReportCreateIn): Promise<ReportOut> {
    const r = await http.post("/api/v1/reports", data);
    return r.data;
  },

  async uploadEvidence(caseId: number, file: File): Promise<EvidenceFileOut> {
    const form = new FormData();
    form.append("file", file);
    const r = await http.post(`/api/v1/reports/${caseId}/evidence`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return r.data;
  },

  async listMyReports(params?: {
    status?: string;
    page?: number;
    size?: number;
  }): Promise<PaginationOut<ReportOut>> {
    const r = await http.get("/api/v1/reports/my", { params });
    return r.data;
  },

  async getReport(caseId: number): Promise<ReportDetailOut> {
    const r = await http.get(`/api/v1/reports/${caseId}`);
    return r.data;
  },

  // Draft APIs
  async createDraft(data: DraftSaveIn): Promise<DraftOut> {
    const r = await http.post("/api/v1/drafts", data);
    return r.data;
  },

  async listDrafts(): Promise<DraftOut[]> {
    const r = await http.get("/api/v1/drafts");
    return r.data;
  },

  async getDraft(draftId: number): Promise<DraftOut> {
    const r = await http.get(`/api/v1/drafts/${draftId}`);
    return r.data;
  },

  async updateDraft(draftId: number, data: DraftSaveIn): Promise<DraftOut> {
    const r = await http.put(`/api/v1/drafts/${draftId}`, data);
    return r.data;
  },

  async deleteDraft(draftId: number): Promise<void> {
    await http.delete(`/api/v1/drafts/${draftId}`);
  },

  async uploadDraftEvidence(draftId: number, file: File): Promise<EvidenceFileOut> {
    const form = new FormData();
    form.append("file", file);
    const r = await http.post(`/api/v1/drafts/${draftId}/evidence`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return r.data;
  },

  async deleteDraftEvidence(draftId: number, fileId: number): Promise<void> {
    await http.delete(`/api/v1/drafts/${draftId}/evidence/${fileId}`);
  },
};

export const STATUS_LABEL: Record<string, string> = {
  PENDING: "待审核",
  REVIEWING: "审核中",
  HANDLED: "已处理",
  REJECTED: "已驳回",
  REPORTED: "已转报警",
};

export const STATUS_TYPE: Record<string, "info" | "warning" | "success" | "danger"> = {
  PENDING: "info",
  REVIEWING: "warning",
  HANDLED: "success",
  REJECTED: "danger",
  REPORTED: "warning",
};
