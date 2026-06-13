import type { PaginationOut } from "./api";

export type WarningLevel = 1 | 2 | 3;
export type WarningPushScope = "FULL_SCHOOL" | "DEPARTMENT";
export type WarningStatus = "ONLINE" | "OFFLINE";

/** 列表项（学生 / 管理端通用精简视图）。 */
export interface WarningListItem {
  warning_id: string;
  title: string;
  warning_level: WarningLevel;
  status: WarningStatus;
  push_scope: WarningPushScope;
  publisher_name: string | null;
  published_at: string;
}

/** 详情（学生端 / 管理端通用）。 */
export interface WarningOut {
  warning_id: string;
  title: string;
  content: string;
  warning_level: WarningLevel;
  push_scope: WarningPushScope;
  publisher_id: string;
  publisher_name: string | null;
  target_dept_ids: number[];
  status: WarningStatus;
  appendix: string | null;
  related_case_no: string | null;
  published_at: string;
  expires_at: string | null;
  offline_at: string | null;
  offline_reason: string | null;
}

/** 学生 / 管理端列表查询。 */
export interface WarningListParams {
  status?: WarningStatus;
  level?: WarningLevel;
  keyword?: string;
  page?: number;
  size?: number;
}

/** 管理端列表查询（多 publisher_id 过滤）。 */
export interface WarningAdminListParams extends WarningListParams {
  publisher_id?: number;
}

/** 发布预警入参。 */
export interface WarningCreateBody {
  title: string;
  content: string;
  warning_level: WarningLevel;
  push_scope: WarningPushScope;
  target_dept_ids?: number[];
  related_case_no?: string | null;
  expires_at?: string | null;
}

/** 追加说明入参（必填）。 */
export interface WarningAppendBody {
  appendix: string;
}

/** 手动下线入参。 */
export interface WarningOfflineBody {
  reason: string;
}

export type WarningPagination = PaginationOut<WarningListItem>;
