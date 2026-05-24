/** 站内通知相关 TypeScript 类型定义。
 *
 * 字段与后端 NotificationOut schema 一一对应。
 * notification_id / related_object_id 均为雪花字符串（后端 coerce_numbers_to_str）。
 */

export interface Notification {
  /** 通知 ID（雪花字符串，对应后端 BigInteger） */
  notification_id: string
  /** 通知类型，如 REPORT_RESOLVED / QUIZ_ASSIGNED / WARNING_PUSH */
  type: string
  /** 通知标题 */
  title: string
  /** 通知正文 */
  content: string
  /** 关联对象类型（如 fraud_case / warning_notice），可为 null */
  related_object_type: string | null
  /** 关联对象 ID（雪花字符串），可为 null */
  related_object_id: string | null
  /** 是否已读 */
  is_read: boolean
  /** 通知创建时间（ISO 8601） */
  created_at: string
  /** 已读时间，未读时为 null */
  read_at: string | null
}

export interface NotificationPage {
  items: Notification[]
  total: number
  page: number
  size: number
}

export interface UnreadCountResponse {
  count: number
}
