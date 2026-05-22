import http from "./http";
import type { PaginationOut } from "@/types/api";
import type {
  KnowledgeAdminListParams,
  KnowledgeCreateBody,
  KnowledgeDetail,
  KnowledgeHistoryItem,
  KnowledgeListItem,
  KnowledgeListParams,
  KnowledgeOfflineBody,
  KnowledgeOut,
  KnowledgeReviewBody,
  KnowledgeUpdateBody,
} from "@/types/knowledge";
export type {
  KnowledgeAdminListParams,
  KnowledgeCreateBody,
  KnowledgeDetail,
  KnowledgeHistoryItem,
  KnowledgeListItem,
  KnowledgeListParams,
  KnowledgeListSort,
  KnowledgeListStatus,
  KnowledgeOfflineBody,
  KnowledgeOut,
  KnowledgePagination,
  KnowledgeReviewAction,
  KnowledgeReviewBody,
  KnowledgeSourceType,
  KnowledgeStatus,
  KnowledgeUpdateBody,
} from "@/types/knowledge";

export const knowledgeApi = {
  /** 学生侧：仅 PUBLISHED 条目浏览。 */
  async listPublic(
    params?: KnowledgeListParams,
  ): Promise<PaginationOut<KnowledgeListItem>> {
    const r = await http.get("/api/v1/knowledge", { params });
    return r.data;
  },

  /** 学生侧：详情 + 同 fraud_type_id 的最近 3 条相关推荐。 */
  async getPublic(entryId: string): Promise<KnowledgeDetail> {
    const r = await http.get(`/api/v1/knowledge/${entryId}`);
    return r.data;
  },

  /** 管理侧：所有状态条目列表（按状态、作者过滤）。 */
  async listAdmin(
    params?: KnowledgeAdminListParams,
  ): Promise<PaginationOut<KnowledgeListItem>> {
    const r = await http.get("/api/v1/admin/knowledge", { params });
    return r.data;
  },

  /** 管理侧：任意状态详情。 */
  async getAdmin(entryId: string): Promise<KnowledgeOut> {
    const r = await http.get(`/api/v1/admin/knowledge/${entryId}`);
    return r.data;
  },

  /** 管理侧：新建草稿。 */
  async create(data: KnowledgeCreateBody): Promise<KnowledgeOut> {
    const r = await http.post("/api/v1/admin/knowledge", data);
    return r.data;
  },

  /** 管理侧：编辑（PATCH 部分字段）。 */
  async update(entryId: string, data: KnowledgeUpdateBody): Promise<KnowledgeOut> {
    const r = await http.patch(`/api/v1/admin/knowledge/${entryId}`, data);
    return r.data;
  },

  /** 管理侧：DRAFT → PENDING（作者本人提交）。 */
  async submit(entryId: string): Promise<KnowledgeOut> {
    const r = await http.post(`/api/v1/admin/knowledge/${entryId}/submit`);
    return r.data;
  },

  /** 管理侧：校级审核（APPROVE → PUBLISHED；REJECT → DRAFT，必填 review_note）。 */
  async review(entryId: string, data: KnowledgeReviewBody): Promise<KnowledgeOut> {
    const r = await http.post(`/api/v1/admin/knowledge/${entryId}/review`, data);
    return r.data;
  },

  /** 管理侧：下线（PUBLISHED → OFFLINE，学生端不可见）。 */
  async offline(
    entryId: string,
    data: KnowledgeOfflineBody,
  ): Promise<{ status: string; entry_id?: string | number }> {
    const r = await http.post(`/api/v1/admin/knowledge/${entryId}/offline`, data);
    return r.data;
  },

  /** 管理侧：历史版本（事件溯源）。 */
  async history(entryId: string): Promise<KnowledgeHistoryItem[]> {
    const r = await http.get(`/api/v1/admin/knowledge/${entryId}/history`);
    return r.data;
  },
};

/** 状态中文标签。 */
export const KNOWLEDGE_STATUS_LABEL: Record<string, string> = {
  DRAFT: "草稿",
  PENDING: "待审核",
  PUBLISHED: "已发布",
  OFFLINE: "已下线",
};

/** 状态 Tag 配色（Element Plus type）。 */
export const KNOWLEDGE_STATUS_TONE: Record<
  string,
  "info" | "warning" | "success" | "danger"
> = {
  DRAFT: "info",
  PENDING: "warning",
  PUBLISHED: "success",
  OFFLINE: "danger",
};

/** 来源类型中文标签。 */
export const KNOWLEDGE_SOURCE_LABEL: Record<string, string> = {
  CASE: "校内案件",
  SCHOOL: "校方公告",
  NATIONAL: "反诈中心",
};

/** 审核动作中文标签。 */
export const KNOWLEDGE_REVIEW_ACTION_LABEL: Record<string, string> = {
  APPROVE: "通过发布",
  REJECT: "驳回回草稿",
};
