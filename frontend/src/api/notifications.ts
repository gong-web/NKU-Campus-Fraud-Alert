/**
 * 通知模块 API 封装。
 *
 * 使用项目统一的 axios 实例（@/api/http），该实例已配置：
 *  - baseURL: VITE_API_BASE_URL
 *  - withCredentials: true（cookie 鉴权）
 *  - X-Requested-With: XMLHttpRequest（CSRF 防护头）
 *
 * 如果项目的 axios 实例导入路径不同，请调整第一行 import。
 */

import http from '@/api/http'
import type { NotificationPage, UnreadCountResponse } from '@/types/notification'

const BASE = '/api/v1/notifications'

/** 获取当前用户通知列表（分页） */
export async function fetchMyNotifications(params: {
  page?: number
  size?: number
  unread_only?: boolean
}): Promise<NotificationPage> {
  const res = await http.get<NotificationPage>(`${BASE}/my`, { params })
  return res.data
}

/** 获取未读通知数量（铃铛红点轮询用） */
export async function fetchUnreadCount(): Promise<number> {
  const res = await http.get<UnreadCountResponse>(`${BASE}/my/unread-count`)
  return res.data.count
}

/** 标记单条通知为已读 */
export async function markNotificationRead(notificationId: string): Promise<boolean> {
  const res = await http.patch<{ success: boolean }>(`${BASE}/${notificationId}/read`)
  return res.data.success
}

/** 一键全部已读，返回实际标记条数 */
export async function markAllNotificationsRead(): Promise<number> {
  const res = await http.patch<{ marked: number }>(`${BASE}/my/read-all`)
  return res.data.marked
}
