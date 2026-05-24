<script setup lang="ts">
/**
 * 站内通知铃铛 + 红点 + 下拉列表。
 *
 * 用法：在每个角色的 Layout 顶部导航栏插入 `<AppNotificationBell />`，
 * 全平台所有页面都能看到。组件自带 30s 未读数轮询，挂载/卸载自动
 * 启停（见 `stores/notifications.ts` 的 startPolling / stopPolling）。
 *
 * 设计要点
 * --------
 * - 未登录态：什么也不渲染（auth.isLoggedIn === false）。
 * - 红点数 99+：超过 99 显示 "99+"。
 * - 点击通知项：标记已读 + 如果有 related_object_* 则跳到对应详情页。
 * - 点击外部关闭下拉：document mousedown 监听。
 */

import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useNotificationStore } from "@/stores/notifications";
import type { Notification } from "@/types/notification";
import AppIcon from "./AppIcon.vue";

const auth = useAuthStore();
const store = useNotificationStore();
const router = useRouter();

const open = ref<boolean>(false);
const rootRef = ref<HTMLElement | null>(null);

const badge = computed<string>(() => {
  const n = store.unreadCount;
  if (n <= 0) return "";
  if (n > 99) return "99+";
  return String(n);
});

function formatTime(iso: string): string {
  // 12 小时内显示相对时间，否则显示绝对日期
  const t = new Date(iso).getTime();
  const diffSec = Math.floor((Date.now() - t) / 1000);
  if (diffSec < 60) return "刚刚";
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} 分钟前`;
  if (diffSec < 86_400) return `${Math.floor(diffSec / 3600)} 小时前`;
  return iso.slice(0, 10);
}

function toggle(): void {
  open.value = !open.value;
  if (open.value) {
    void store.fetchList(1);
  }
}

function closePanel(): void {
  open.value = false;
}

async function onItemClick(item: Notification): Promise<void> {
  // 1. 标记已读（乐观更新）
  if (!item.is_read) {
    await store.markRead(item.notification_id);
  }
  // 2. 跳转：根据 related_object_type 路由到对应详情
  const dest = resolveTarget(item);
  closePanel();
  if (dest) {
    await router.push(dest);
  }
}

interface RouterTarget {
  name: string;
  params?: Record<string, string>;
}

function resolveTarget(item: Notification): RouterTarget | null {
  if (!item.related_object_type || !item.related_object_id) return null;
  const id = item.related_object_id;
  const role = auth.role;
  switch (item.related_object_type) {
    case "fraud_case":
      if (role === "STUDENT") {
        return { name: "report-detail", params: { case_id: id } };
      }
      if (role === "REVIEWER" || role === "SYS_ADMIN") {
        return { name: "admin-report-detail", params: { case_id: id } };
      }
      return null;
    case "warning_notice":
      if (role === "STUDENT") {
        return { name: "warning-detail", params: { warning_id: id } };
      }
      return { name: "admin-warning-detail", params: { warning_id: id } };
    case "knowledge_entry":
      if (role === "STUDENT") {
        return { name: "kb-detail", params: { entry_id: id } };
      }
      return { name: "admin-kb-detail", params: { entry_id: id } };
    case "quiz":
      if (role === "STUDENT") {
        return { name: "student-quiz-take", params: { quiz_id: id } };
      }
      return { name: "admin-quiz-report", params: { quiz_id: id } };
    default:
      return null;
  }
}

async function markAll(): Promise<void> {
  await store.markAllRead();
}

function onDocMouseDown(evt: MouseEvent): void {
  if (!open.value) return;
  const t = evt.target as Node | null;
  if (rootRef.value && t && !rootRef.value.contains(t)) {
    closePanel();
  }
}

watch(
  () => auth.isLoggedIn,
  (next) => {
    if (next) {
      store.startPolling();
    } else {
      store.stopPolling();
    }
  },
  { immediate: false },
);

onMounted(() => {
  document.addEventListener("mousedown", onDocMouseDown);
  if (auth.isLoggedIn) store.startPolling();
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocMouseDown);
  store.stopPolling();
});
</script>

<template>
  <div
    v-if="auth.isLoggedIn"
    ref="rootRef"
    class="app-bell"
  >
    <button
      type="button"
      class="app-bell__trigger"
      :aria-label="`通知中心，${badge ? badge + ' 条未读' : '无未读'}`"
      :aria-expanded="open"
      @click="toggle"
    >
      <AppIcon
        name="bell"
        :size="18"
      />
      <span
        v-if="badge"
        class="app-bell__badge"
        aria-hidden="true"
      >{{ badge }}</span>
    </button>

    <transition name="app-bell-fade">
      <div
        v-if="open"
        class="app-bell__panel"
        role="dialog"
        aria-label="通知中心"
      >
        <header class="app-bell__head">
          <strong>通知中心</strong>
          <button
            type="button"
            class="app-bell__link"
            :disabled="store.unreadCount === 0"
            @click="markAll"
          >
            全部已读
          </button>
        </header>
        <div
          v-if="store.loading"
          class="app-bell__hint"
        >
          加载中…
        </div>
        <ul
          v-else-if="store.list.length > 0"
          class="app-bell__list"
        >
          <li
            v-for="item in store.list"
            :key="item.notification_id"
            class="app-bell__item"
            :class="{ 'app-bell__item--unread': !item.is_read }"
            @click="onItemClick(item)"
          >
            <div class="app-bell__item-row">
              <span
                class="app-bell__dot"
                :class="{ 'app-bell__dot--unread': !item.is_read }"
                aria-hidden="true"
              />
              <strong class="app-bell__title">{{ item.title }}</strong>
              <span class="app-bell__time">{{ formatTime(item.created_at) }}</span>
            </div>
            <p class="app-bell__content">
              {{ item.content }}
            </p>
          </li>
        </ul>
        <div
          v-else
          class="app-bell__hint"
        >
          暂无通知
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.app-bell {
  position: relative;
  display: inline-flex;
}

.app-bell__trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-out);
}

.app-bell__trigger:hover {
  color: var(--color-brand-700);
  border-color: var(--color-brand-300);
  box-shadow: 0 0 0 3px rgb(134 38 51 / 8%);
}

.app-bell__badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--color-danger, #c62828);
  color: #fff;
  font-size: 11px;
  line-height: 18px;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 0 0 2px var(--color-surface);
}

.app-bell__panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  max-height: 460px;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-mid);
  z-index: var(--z-dropdown, 1100);
  overflow: hidden;
}

.app-bell__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.app-bell__head strong {
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
}

.app-bell__link {
  background: none;
  border: none;
  color: var(--color-brand-600);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.app-bell__link:disabled {
  color: var(--color-text-tertiary);
  cursor: not-allowed;
}

.app-bell__list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  max-height: 400px;
}

.app-bell__item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-soft, var(--color-border));
  cursor: pointer;
  transition: background var(--duration-base) var(--easing-out);
}

.app-bell__item:last-child {
  border-bottom: none;
}

.app-bell__item:hover {
  background: var(--color-brand-50, #fff7f0);
}

.app-bell__item--unread {
  background: rgb(134 38 51 / 4%);
}

.app-bell__item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.app-bell__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: transparent;
  flex-shrink: 0;
}

.app-bell__dot--unread {
  background: var(--color-danger, #c62828);
  box-shadow: 0 0 6px rgb(198 40 40 / 60%);
}

.app-bell__title {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-strong);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-bell__time {
  font-size: 11px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.app-bell__content {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.app-bell__hint {
  padding: 32px 16px;
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

/* 动画 */
.app-bell-fade-enter-active,
.app-bell-fade-leave-active {
  transition:
    opacity var(--duration-base) var(--easing-out),
    transform var(--duration-base) var(--easing-out);
}

.app-bell-fade-enter-from,
.app-bell-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
