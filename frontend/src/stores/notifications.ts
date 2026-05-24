/**
 * 通知 Pinia Store。
 *
 * 职责：
 *  - 维护未读数（unreadCount）—— 每 30 秒轮询一次，驱动铃铛红点
 *  - 维护通知列表（list）—— 用户展开铃铛时按需拉取
 *  - 提供 markRead / markAllRead action
 *
 * 使用方式：
 *  在布局组件的 AppNotificationBell 里 onMounted 调 startPolling，
 *  onUnmounted 调 stopPolling，确保每个角色的布局各管自己生命周期。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  fetchMyNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/api/notifications'
import type { Notification } from '@/types/notification'

const POLL_INTERVAL_MS = 30_000 // 30 秒轮询一次

export const useNotificationStore = defineStore('notifications', () => {
  // ── state ────────────────────────────────────────────────────────
  const unreadCount = ref<number>(0)
  const list = ref<Notification[]>([])
  const total = ref<number>(0)
  const page = ref<number>(1)
  const size = ref<number>(20)
  const loading = ref<boolean>(false)

  let _pollTimer: ReturnType<typeof setInterval> | null = null

  // ── actions ──────────────────────────────────────────────────────

  /** 拉取未读数（轮询调用） */
  async function fetchCount(): Promise<void> {
    try {
      unreadCount.value = await fetchUnreadCount()
    } catch {
      // 静默失败：网络抖动时不弹错误，等下次轮询
    }
  }

  /** 拉取通知列表（点开铃铛时调用） */
  async function fetchList(pageNum = 1): Promise<void> {
    loading.value = true
    try {
      const data = await fetchMyNotifications({ page: pageNum, size: size.value })
      list.value = data.items
      total.value = data.total
      page.value = data.page
    } catch {
      // 保留上次数据，不清空
    } finally {
      loading.value = false
    }
  }

  /** 标记单条已读，乐观更新本地列表 */
  async function markRead(notificationId: string): Promise<void> {
    // 乐观更新：先本地改，再发请求
    const item = list.value.find((n) => n.notification_id === notificationId)
    if (item && !item.is_read) {
      item.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
    try {
      await markNotificationRead(notificationId)
    } catch {
      // 如果请求失败则回滚本地状态
      if (item) item.is_read = false
      unreadCount.value = await fetchUnreadCount()
    }
  }

  /** 一键全部已读，乐观更新 */
  async function markAllRead(): Promise<void> {
    const prevCount = unreadCount.value
    list.value.forEach((n) => (n.is_read = true))
    unreadCount.value = 0
    try {
      await markAllNotificationsRead()
    } catch {
      // 回滚
      await fetchList(page.value)
      unreadCount.value = prevCount
    }
  }

  // ── 轮询控制 ─────────────────────────────────────────────────────

  /** 启动未读数轮询（在布局组件 onMounted 调用） */
  function startPolling(): void {
    if (_pollTimer !== null) return // 防止重复启动
    fetchCount() // 立即拉一次，不等第一个 interval
    _pollTimer = setInterval(fetchCount, POLL_INTERVAL_MS)
  }

  /** 停止轮询（在布局组件 onUnmounted 调用） */
  function stopPolling(): void {
    if (_pollTimer !== null) {
      clearInterval(_pollTimer)
      _pollTimer = null
    }
  }

  return {
    // state（只读暴露）
    unreadCount,
    list,
    total,
    page,
    size,
    loading,
    // actions
    fetchCount,
    fetchList,
    markRead,
    markAllRead,
    startPolling,
    stopPolling,
  }
})
