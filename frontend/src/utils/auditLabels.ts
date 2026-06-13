/** 审计操作类型 → 界面展示文案 */
export const AUDIT_OP_LABELS: Record<string, string> = {
  LOGIN: "登录",
  LOGIN_FAILED: "登录失败",
  LOGOUT: "登出",
  USER_CREATE: "创建账号",
  USER_DISABLE: "停用账号",
  USER_ENABLE: "启用账号",
  USER_ROLE_CHANGE: "变更角色",
  USER_BATCH_IMPORT: "批量导入账号",
  DECRYPT_ANONYMOUS: "司法解密",
  DECRYPT_ANONYMOUS_REQUEST: "司法协助申请",
};

export function auditOpLabel(op: string): string {
  return AUDIT_OP_LABELS[op] ?? op;
}

export const AUDIT_OBJECT_TYPE_LABELS: Record<string, string> = {
  user: "账号",
  report: "上报事件",
  audit_log: "审计记录",
  judicial_request: "司法协助",
};

export function auditObjectTypeLabel(type: string): string {
  return AUDIT_OBJECT_TYPE_LABELS[type] ?? type;
}
