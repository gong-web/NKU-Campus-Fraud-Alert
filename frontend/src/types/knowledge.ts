import type { PaginationOut } from "./api";

export type KnowledgeStatus = "DRAFT" | "PENDING" | "PUBLISHED" | "OFFLINE";
export type KnowledgeListStatus = KnowledgeStatus | "ALL";
export type KnowledgeSourceType = "CASE" | "SCHOOL" | "NATIONAL";
export type KnowledgeReviewAction = "APPROVE" | "REJECT";
export type KnowledgeListSort = "published_at_desc" | "hot";

/** 列表项（不含完整 prevention_advice，体积更小）。 */
export interface KnowledgeListItem {
  entry_id: string;
  title: string;
  fraud_type_id: number;
  fraud_type_name: string | null;
  desensitized_summary: string;
  status: KnowledgeStatus;
  version: number;
  author_id: string;
  author_name: string | null;
  published_at: string | null;
  updated_at: string;
}

/** 条目详情。 */
export interface KnowledgeOut {
  entry_id: string;
  title: string;
  fraud_type_id: number;
  fraud_type_name: string | null;
  desensitized_summary: string;
  identification_points: string;
  prevention_advice: string;
  peak_periods: string | null;
  source_type: KnowledgeSourceType;
  source_reference: string | null;
  status: KnowledgeStatus;
  version: number;
  author_id: string;
  author_name: string | null;
  reviewer_id: string | null;
  reviewer_name: string | null;
  review_note: string | null;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  offlined_at: string | null;
}

/** 学生端详情：含同 fraud_type_id 的最近 3 条相关推荐（不含本身）。 */
export interface KnowledgeDetail extends KnowledgeOut {
  related: KnowledgeListItem[];
}

/** 学生 / 管理端通用列表查询。 */
export interface KnowledgeListParams {
  keyword?: string;
  fraud_type_id?: number;
  page?: number;
  size?: number;
  sort?: KnowledgeListSort;
}

/** 管理端列表查询（多状态、按作者过滤）。 */
export interface KnowledgeAdminListParams {
  status?: KnowledgeListStatus[];
  keyword?: string;
  fraud_type_id?: number;
  author_id?: number;
  page?: number;
  size?: number;
}

/** 新建知识库条目入参。 */
export interface KnowledgeCreateBody {
  title: string;
  fraud_type_id: number;
  desensitized_summary: string;
  identification_points: string;
  prevention_advice: string;
  peak_periods?: string | null;
  source_type?: KnowledgeSourceType;
  source_reference?: string | null;
}

/** 编辑条目入参（PATCH，全部可选）。 */
export type KnowledgeUpdateBody = Partial<KnowledgeCreateBody>;

/** 校级审核入参（REJECT 时 review_note 必填）。 */
export interface KnowledgeReviewBody {
  action: KnowledgeReviewAction;
  review_note?: string | null;
}

/** 下线入参。 */
export interface KnowledgeOfflineBody {
  reason: string;
}

/** 历史版本快照（事件溯源）。 */
export interface KnowledgeHistoryItem {
  history_id: string;
  entry_id: string;
  version: number;
  action: string;
  modified_by: string;
  modified_at: string;
  content_snapshot: Record<string, unknown> | null;
}

export type KnowledgePagination = PaginationOut<KnowledgeListItem>;
