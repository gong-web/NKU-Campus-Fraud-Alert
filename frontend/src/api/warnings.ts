import http from "./http";
import type { PaginationOut } from "@/types/api";
import type {
  WarningAdminListParams,
  WarningAppendBody,
  WarningCreateBody,
  WarningListItem,
  WarningListParams,
  WarningOfflineBody,
  WarningOut,
} from "@/types/warning";
export type {
  WarningAdminListParams,
  WarningAppendBody,
  WarningCreateBody,
  WarningLevel,
  WarningListItem,
  WarningListParams,
  WarningOfflineBody,
  WarningOut,
  WarningPagination,
  WarningPushScope,
  WarningStatus,
} from "@/types/warning";

export const warningsApi = {
  /** 学生侧：本人可见预警列表（FULL_SCHOOL + 本院系命中）。 */
  async listMine(params?: WarningListParams): Promise<PaginationOut<WarningListItem>> {
    const r = await http.get("/api/v1/warnings", { params });
    return r.data;
  },

  /** 学生侧：预警详情。 */
  async getMine(warningId: string): Promise<WarningOut> {
    const r = await http.get(`/api/v1/warnings/${warningId}`);
    return r.data;
  },

  /** 管理侧：发布预警（紧急级仅校级 reviewer 可发）。 */
  async publish(data: WarningCreateBody): Promise<WarningOut> {
    const r = await http.post("/api/v1/admin/warnings", data);
    return r.data;
  },

  /** 管理侧：所有预警（含 OFFLINE）列表。 */
  async listAdmin(
    params?: WarningAdminListParams,
  ): Promise<PaginationOut<WarningListItem>> {
    const r = await http.get("/api/v1/admin/warnings", { params });
    return r.data;
  },

  /** 管理侧：详情。 */
  async getAdmin(warningId: string): Promise<WarningOut> {
    const r = await http.get(`/api/v1/admin/warnings/${warningId}`);
    return r.data;
  },

  /** 管理侧：追加后续说明（仅 ONLINE 状态可用，OFFLINE 触发 409）。 */
  async append(warningId: string, data: WarningAppendBody): Promise<WarningOut> {
    const r = await http.post(`/api/v1/admin/warnings/${warningId}/append`, data);
    return r.data;
  },

  /** 管理侧：手动下线（重复下线触发 409）。 */
  async offline(
    warningId: string,
    data: WarningOfflineBody,
  ): Promise<{ status: string }> {
    const r = await http.post(`/api/v1/admin/warnings/${warningId}/offline`, data);
    return r.data;
  },
};

/** 等级中文标签。 */
export const WARNING_LEVEL_LABEL: Record<number, string> = {
  1: "提示",
  2: "警告",
  3: "紧急",
};

/** 等级 Tag 配色（Element Plus type）。 */
export const WARNING_LEVEL_TONE: Record<
  number,
  "info" | "warning" | "danger" | "success"
> = {
  1: "info",
  2: "warning",
  3: "danger",
};

/** 状态中文标签。 */
export const WARNING_STATUS_LABEL: Record<string, string> = {
  ONLINE: "上线中",
  OFFLINE: "已下线",
};

/** 状态 Tag 配色。 */
export const WARNING_STATUS_TONE: Record<
  string,
  "info" | "warning" | "danger" | "success"
> = {
  ONLINE: "success",
  OFFLINE: "info",
};

/** 推送范围中文标签。 */
export const WARNING_SCOPE_LABEL: Record<string, string> = {
  FULL_SCHOOL: "全校",
  DEPARTMENT: "按院系",
};
