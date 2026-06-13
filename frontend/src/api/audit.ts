import http from "./http";
import type { AuditLogOut, PaginationOut } from "@/types/api";
import { downloadBlob } from "@/utils/download";

export interface AuditExportParams {
  op_type?: string;
  operator_id?: string;
  object_type?: string;
  object_id?: string;
  start?: string;
  end?: string;
}

export const auditApi = {
  async list(params: {
    op_type?: string;
    operator_id?: string;
    object_type?: string;
    object_id?: string;
    start?: string;
    end?: string;
    page?: number;
    size?: number;
  } = {}): Promise<PaginationOut<AuditLogOut>> {
    const r = await http.get("/api/v1/audit-logs", { params });
    return r.data;
  },

  async byObject(object_type: string, object_id: string): Promise<AuditLogOut[]> {
    const r = await http.get("/api/v1/audit-logs/by-object", {
      params: { object_type, object_id },
    });
    return r.data;
  },

  async exportCsv(params: AuditExportParams = {}): Promise<void> {
    const r = await http.get("/api/v1/audit-logs/export", {
      params,
      responseType: "blob",
    });
    downloadBlob(
      r.data as unknown as Blob,
      r.headers?.["content-disposition"] as string | undefined,
      "audit_logs.csv",
    );
  },
};
