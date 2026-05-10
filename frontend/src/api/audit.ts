import http from "./http";
import type { AuditLogOut, PaginationOut } from "@/types/api";

export const auditApi = {
  async list(params: {
    op_type?: string;
    operator_id?: number;
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
};
