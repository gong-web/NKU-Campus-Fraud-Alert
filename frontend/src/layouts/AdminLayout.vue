<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { AppIcon, BrandLogo } from "@/components";
import AppNotificationBell from "@/components/AppNotificationBell.vue";

const router = useRouter();
const auth = useAuthStore();

interface NavItem {
  to: string;
  label: string;
  icon: string;
  description: string;
}

const NAV: readonly NavItem[] = [
  { to: "/admin/dashboard", label: "工作台", icon: "activity", description: "待处理事件总览" },
  { to: "/admin/reports", label: "审核队列", icon: "clipboard-list", description: "筛选、查看并处理案件" },
  { to: "/admin/warnings", label: "预警公告", icon: "bell", description: "发布与维护安全预警" },
  { to: "/admin/kb", label: "知识库", icon: "book-open", description: "撰写与审核反诈知识" },
  { to: "/admin/quiz", label: "安全测验", icon: "check-circle", description: "题库 · 指定测验 · 完成率报告" },
];

const initial = computed<string>(() => {
  const name = auth.me?.real_name || "?";
  return Array.from(name)[0] ?? "?";
});

async function handleLogout(): Promise<void> {
  try {
    const url = await auth.logout();
    if (url && /^https?:\/\//i.test(url)) {
      window.location.href = url;
      return;
    }
  } catch {
    // 即使 logout 接口失败也照样退到登录页（本地会话已清）
  }
  await router.replace({ name: "login" });
}
</script>

<template>
  <div class="admin-layout">
    <aside
      class="admin-layout__sidebar"
      aria-label="主导航"
    >
      <div class="admin-layout__sidebar-grid" />
      <div class="admin-layout__sidebar-noise" />
      <span class="admin-layout__sidebar-motto">允公允能</span>

      <div class="admin-layout__brand">
        <BrandLogo
          :size="34"
          variant="white"
          :with-text="true"
        />
      </div>

      <div class="admin-layout__nav-label">
        <span>审核台</span>
        <span class="admin-layout__nav-divider" />
      </div>

      <nav class="admin-layout__nav">
        <RouterLink
          v-for="item in NAV"
          :key="item.to"
          :to="item.to"
          class="admin-layout__link"
        >
          <span
            class="admin-layout__link-bar"
            aria-hidden="true"
          />
          <span class="admin-layout__link-icon">
            <AppIcon
              :name="(item.icon as never)"
              :size="18"
            />
          </span>
          <span class="admin-layout__link-text">
            <strong>{{ item.label }}</strong>
            <small>{{ item.description }}</small>
          </span>
        </RouterLink>
      </nav>

      <div class="admin-layout__sidebar-foot">
        <div class="admin-layout__sidebar-card">
          <span class="admin-layout__sidebar-card-icon">
            <AppIcon
              name="info"
              :size="14"
            />
          </span>
          <div>
            <strong>双轨审核</strong>
            <small>院系级 · 校级 · 状态机闭环</small>
          </div>
        </div>
        <div class="admin-layout__sidebar-stamp">
          NK · 审核 2026
        </div>
      </div>
    </aside>

    <div class="admin-layout__main">
      <header class="admin-layout__header">
        <div class="admin-layout__crumb">
          <AppIcon
            name="list-checks"
            :size="14"
            class="admin-layout__crumb-icon"
          />
          <span>审核台</span>
          <AppIcon
            name="chevron-right"
            :size="14"
          />
          <strong>{{ $route.meta.title || "工作台" }}</strong>
        </div>
        <div class="admin-layout__user">
          <AppNotificationBell />
          <div class="admin-layout__user-meta">
            <strong>{{ auth.me?.real_name || "未登录" }}</strong>
            <small>审核管理员</small>
          </div>
          <span
            class="admin-layout__avatar"
            aria-hidden="true"
          >
            {{ initial }}
            <span class="admin-layout__avatar-dot" />
          </span>
          <button
            type="button"
            class="admin-layout__logout"
            @click="handleLogout"
          >
            <AppIcon
              name="log-out"
              :size="14"
            />
            退出
          </button>
        </div>
      </header>
      <main class="admin-layout__content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: grid;
  grid-template-columns: 248px 1fr;
  min-height: 100vh;
  background: var(--color-bg);
}

.admin-layout__sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, #232938 0%, #131722 60%, #0a0d14 100%);
  color: var(--color-neutral-0);
  padding: var(--space-5) var(--space-3);
  overflow: hidden;
}

.admin-layout__sidebar-grid {
  position: absolute;
  inset: 0;
  background-image: var(--pattern-grid);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse at top, black 30%, transparent 80%);
  pointer-events: none;
  opacity: 0.7;
}

.admin-layout__sidebar-noise {
  position: absolute;
  inset: 0;
  background-image:
    var(--pattern-lotus),
    var(--pattern-noise);
  background-size: 220px 220px, 160px 160px;
  background-position: 50% 70%;
  opacity: 0.45;
  mix-blend-mode: overlay;
  pointer-events: none;
}

.admin-layout__sidebar-motto {
  position: absolute;
  bottom: 28%;
  left: 0;
  right: 0;
  text-align: center;
  font-family: var(--font-family-serif);
  font-size: 56px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.18em;
  color: rgb(255 255 255 / 4%);
  pointer-events: none;
  user-select: none;
}

.admin-layout__brand {
  position: relative;
  padding: var(--space-3);
  margin-bottom: var(--space-5);
}

.admin-layout__nav-label {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3);
  margin-bottom: var(--space-2);
  font-size: 10.5px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  font-weight: var(--font-weight-medium);
  color: rgb(255 233 196 / 56%);
}

.admin-layout__nav-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(
    to right,
    rgb(230 179 73 / 32%),
    transparent
  );
}

.admin-layout__nav {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.admin-layout__link {
  position: relative;
  display: grid;
  grid-template-columns: 32px 1fr;
  align-items: center;
  gap: var(--space-2);
  padding: 10px var(--space-3);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: rgb(255 255 255 / 78%);
  border: 1px solid transparent;
  transition: all var(--duration-base) var(--easing-out);
}

.admin-layout__link-bar {
  position: absolute;
  left: -2px;
  top: 50%;
  width: 3px;
  height: 0;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--color-gold-200), var(--color-gold-500));
  transform: translateY(-50%);
  transition: height var(--duration-base) var(--easing-out);
  box-shadow: 0 0 12px rgb(230 179 73 / 56%);
}

.admin-layout__link:hover {
  background: rgb(255 255 255 / 6%);
  color: #fff;
}

.admin-layout__link.router-link-active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: rgb(255 255 255 / 10%);
  box-shadow: var(--shadow-glow-brand);
}

.admin-layout__link.router-link-active .admin-layout__link-bar {
  height: 22px;
}

.admin-layout__link-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: rgb(255 255 255 / 8%);
  border: 1px solid rgb(255 255 255 / 8%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base) var(--easing-out);
}

.admin-layout__link.router-link-active .admin-layout__link-icon {
  background: rgb(230 179 73 / 22%);
  border-color: rgb(230 179 73 / 40%);
  color: var(--color-gold-200);
}

.admin-layout__link.router-link-active strong {
  text-shadow: 0 1px 2px rgb(31 8 11 / 32%);
}

.admin-layout__link-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-layout__link-text strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.admin-layout__link-text small {
  font-size: 11px;
  opacity: 0.7;
  margin-top: 2px;
}

.admin-layout__sidebar-foot {
  position: relative;
  margin-top: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid rgb(255 255 255 / 10%);
}

.admin-layout__sidebar-card {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: var(--space-3);
  padding: var(--space-3);
  background: rgb(255 255 255 / 4%);
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: var(--radius-md);
  align-items: center;
}

.admin-layout__sidebar-card-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: rgb(21 101 192 / 24%);
  color: #b8d4f5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.admin-layout__sidebar-card strong {
  display: block;
  font-size: 12px;
  font-weight: var(--font-weight-semibold);
  color: #fff;
}

.admin-layout__sidebar-card small {
  font-size: 10.5px;
  color: rgb(255 255 255 / 56%);
  line-height: 1.4;
}

.admin-layout__sidebar-stamp {
  font-family: var(--font-family-mono);
  font-size: 10px;
  letter-spacing: 0.32em;
  color: rgb(230 179 73 / 56%);
  text-align: center;
}

/* ── 主区 ─────────────────────────────────────────────────────── */
.admin-layout__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-layout__header {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  background: var(--glass-surface-strong);
  backdrop-filter: blur(var(--glass-blur));
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-3) var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.admin-layout__crumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.admin-layout__crumb-icon {
  color: var(--color-brand-500);
}

.admin-layout__crumb strong {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.admin-layout__user {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.admin-layout__user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 11px;
  color: var(--color-text-secondary);
  letter-spacing: 0.06em;
}

.admin-layout__user-meta strong {
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  letter-spacing: 0;
}

.admin-layout__avatar {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-family-serif);
  font-weight: var(--font-weight-bold);
  box-shadow:
    var(--shadow-glow-brand),
    inset 0 0 0 1px rgb(255 255 255 / 18%);
}

.admin-layout__avatar-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow:
    0 0 0 2px var(--color-surface),
    0 0 8px rgb(46 125 50 / 60%);
}

.admin-layout__logout {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 7px var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: inherit;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  transition: all var(--duration-base) var(--easing-out);
}

.admin-layout__logout:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
  box-shadow: 0 0 0 3px rgb(198 40 40 / 10%);
}

.admin-layout__content {
  flex: 1;
  padding: var(--space-6) clamp(var(--space-5), 3.5vw, var(--space-7));
  overflow: auto;
}

@media (width <= 1024px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-layout__sidebar {
    display: none;
  }

  .admin-layout__content {
    padding: var(--space-4);
  }
}
</style>
