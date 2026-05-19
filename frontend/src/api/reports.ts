import http from "./http";
import type { PaginationOut } from "@/types/api";
import type {
  AdminReportDetail,
  AdminReportListItem,
  AdminReportListParams,
  AnonymousDecryptIn,
  AnonymousDecryptOut,
  ContactInfoOut,
  DashboardSummaryOut,
  DraftOut,
  DraftSaveIn,
  EvidenceFileOut,
  FraudType,
  RejectReportIn,
  ReportCreateIn,
  ReportDetailOut,
  ReportOut,
  ResolveReportIn,
  TransferReportIn,
} from "@/types/report";
export type {
  AdminReportDetail,
  AdminReportListItem,
  AdminReportListParams,
  AnonymousDecryptIn,
  AnonymousDecryptOut,
  ContactInfoOut,
  DashboardSummaryOut,
  DraftOut,
  DraftSaveIn,
  EvidenceFileOut,
  FraudType,
  RejectReportIn,
  ReportCreateIn,
  ReportDetailOut,
  ReportOut,
  ResolveReportIn,
  TransferReportIn,
} from "@/types/report";

export const reportsApi = {
  async listFraudTypes(): Promise<FraudType[]> {
    const r = await http.get("/api/v1/fraud-types");
    return r.data;
  },

  async createReport(data: ReportCreateIn): Promise<ReportOut> {
    const r = await http.post("/api/v1/reports", data);
    return r.data;
  },

  async uploadEvidence(caseId: string, file: File): Promise<EvidenceFileOut> {
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

  async getReport(caseId: string): Promise<ReportDetailOut> {
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

  async getDraft(draftId: string): Promise<DraftOut> {
    const r = await http.get(`/api/v1/drafts/${draftId}`);
    return r.data;
  },

  async updateDraft(draftId: string, data: DraftSaveIn): Promise<DraftOut> {
    const r = await http.put(`/api/v1/drafts/${draftId}`, data);
    return r.data;
  },

  async deleteDraft(draftId: string): Promise<void> {
    await http.delete(`/api/v1/drafts/${draftId}`);
  },

  async uploadDraftEvidence(draftId: string, file: File): Promise<EvidenceFileOut> {
    const form = new FormData();
    form.append("file", file);
    const r = await http.post(`/api/v1/drafts/${draftId}/evidence`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return r.data;
  },

  async deleteDraftEvidence(draftId: string, fileId: string): Promise<void> {
    await http.delete(`/api/v1/drafts/${draftId}/evidence/${fileId}`);
  },

  async getDraftEvidenceBlob(draftId: string, fileId: string): Promise<Blob> {
    const r = await http.get(`/api/v1/drafts/${draftId}/evidence/${fileId}`, {
      responseType: "blob",
    });
    return r.data;
  },

  async listAdminReports(params?: AdminReportListParams): Promise<PaginationOut<AdminReportListItem>> {
    const query = {
      ...params,
      status: params?.status,
    };
    const r = await http.get("/api/v1/admin/reports", { params: query });
    return r.data;
  },

  async getAdminReport(caseId: string): Promise<AdminReportDetail> {
    const r = await http.get(`/api/v1/admin/reports/${caseId}`);
    return r.data;
  },

  async resolveAdminReport(caseId: string, data: ResolveReportIn): Promise<{ entry_id: string; status: string }> {
    const r = await http.post(`/api/v1/admin/reports/${caseId}/resolve`, data);
    return r.data;
  },

  async rejectAdminReport(caseId: string, data: RejectReportIn): Promise<{ status: string }> {
    const r = await http.post(`/api/v1/admin/reports/${caseId}/reject`, data);
    return r.data;
  },

  async transferAdminReport(caseId: string, data: TransferReportIn): Promise<{ status: string }> {
    const r = await http.post(`/api/v1/admin/reports/${caseId}/transfer`, data);
    return r.data;
  },

  async requestContactInfo(caseId: string): Promise<ContactInfoOut> {
    const r = await http.post(`/api/v1/admin/reports/${caseId}/contact-request`);
    return r.data;
  },

  async viewEvidence(caseId: string, fileId: string): Promise<Blob> {
    const r = await http.get(`/api/v1/admin/reports/${caseId}/evidence/${fileId}`, {
      responseType: "blob",
      headers: { "X-Confirm-Sensitive-Access": "yes" },
    });
    return r.data;
  },

  async decryptAnonymous(caseId: string, data: AnonymousDecryptIn): Promise<AnonymousDecryptOut> {
    const r = await http.post(`/api/v1/admin/reports/${caseId}/decrypt-anonymous`, data);
    return r.data;
  },

  async getAdminDashboardSummary(): Promise<DashboardSummaryOut> {
    const r = await http.get("/api/v1/admin/dashboard/summary");
    return r.data;
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
