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
  danger?: boolean;
}

const NAV: readonly NavItem[] = [
  { to: "/sys/dashboard", label: "概览", icon: "activity" },
  { to: "/sys/users", label: "账号管理", icon: "users" },
  { to: "/sys/audit", label: "审计日志", icon: "list-checks" },
  { to: "/sys/judicial-assist", label: "司法协助查询", icon: "scale", danger: true },
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
  <div class="sys-layout">
    <aside
      class="sys-layout__sidebar"
      aria-label="主导航"
    >
      <div class="sys-layout__sidebar-grid" />
      <div class="sys-layout__sidebar-noise" />
      <span class="sys-layout__sidebar-motto">
        允公允能<br>
        日新月异
      </span>

      <div class="sys-layout__brand">
        <BrandLogo
          :size="34"
          variant="white"
          :with-text="true"
        />
      </div>

      <div class="sys-layout__nav-label">
        <span>导航</span>
        <span class="sys-layout__nav-divider" />
      </div>

      <nav class="sys-layout__nav">
        <RouterLink
          v-for="item in NAV"
          :key="item.to"
          :to="item.to"
          class="sys-layout__link"
          :class="{ 'sys-layout__link--danger': item.danger }"
        >
          <span
            class="sys-layout__link-bar"
            aria-hidden="true"
          />
          <span class="sys-layout__link-icon">
            <AppIcon
              :name="(item.icon as never)"
              :size="18"
            />
          </span>
          <span class="sys-layout__link-text">
            <strong>{{ item.label }}</strong>
          </span>
          <AppIcon
            name="chevron-right"
            :size="14"
            class="sys-layout__link-arrow"
          />
        </RouterLink>
      </nav>

    </aside>

    <div class="sys-layout__main">
      <header class="sys-layout__header">
        <div class="sys-layout__crumb">
          <strong>{{ $route.meta.title || "概览" }}</strong>
        </div>
        <div class="sys-layout__user">
          <AppNotificationBell />
          <div class="sys-layout__user-meta">
            <strong>{{ auth.me?.real_name || "未登录" }}</strong>
          </div>
          <span
            class="sys-layout__avatar"
            aria-hidden="true"
          >
            {{ initial }}
          </span>
          <button
            type="button"
            class="sys-layout__logout"
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
      <main class="sys-layout__content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.sys-layout {
  display: grid;
  grid-template-columns: 268px 1fr;
  min-height: 100vh;
  background: var(--color-bg);
}

.sys-layout__sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--gradient-aurora);
  color: var(--color-neutral-0);
  padding: var(--space-5) var(--space-3);
  overflow: hidden;
}

.sys-layout__sidebar-grid {
  position: absolute;
  inset: 0;
  background-image: var(--pattern-grid);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse at top, black 30%, transparent 80%);
  pointer-events: none;
}

.sys-layout__sidebar-noise {
  position: absolute;
  inset: 0;
  background-image:
    var(--pattern-lotus),
    var(--pattern-noise);
  background-size: 220px 220px, 160px 160px;
  background-position: 50% 70%;
  opacity: 0.5;
  mix-blend-mode: overlay;
  pointer-events: none;
}

.sys-layout__sidebar-motto {
  position: absolute;
  bottom: 30%;
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

.sys-layout__brand {
  position: relative;
  padding: var(--space-3);
  margin-bottom: var(--space-5);
}

.sys-layout__nav-label {
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

.sys-layout__nav-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(
    to right,
    rgb(230 179 73 / 32%),
    transparent
  );
}

.sys-layout__nav {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.sys-layout__link {
  position: relative;
  display: grid;
  grid-template-columns: 36px 1fr 14px;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: rgb(255 255 255 / 78%);
  border: 1px solid transparent;
  transition:
    background var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out),
    color var(--duration-fast) var(--easing-out),
    transform var(--duration-fast) var(--easing-out);
}

.sys-layout__link-bar {
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

.sys-layout__link:hover {
  background: rgb(255 255 255 / 6%);
  color: var(--color-neutral-0);
}

.sys-layout__link.router-link-active {
  background:
    linear-gradient(120deg, rgb(255 255 255 / 14%) 0%, rgb(255 255 255 / 6%) 100%);
  border-color: rgb(255 255 255 / 22%);
  color: var(--color-neutral-0);
  box-shadow: var(--shadow-low), inset 0 1px 0 rgb(255 255 255 / 14%);
}

.sys-layout__link.router-link-active .sys-layout__link-bar {
  height: 22px;
}

.sys-layout__link-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: rgb(255 255 255 / 8%);
  border: 1px solid rgb(255 255 255 / 8%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base) var(--easing-out);
}

.sys-layout__link:hover .sys-layout__link-icon {
  background: rgb(230 179 73 / 14%);
  border-color: rgb(230 179 73 / 28%);
  color: var(--color-gold-200);
}

.sys-layout__link.router-link-active .sys-layout__link-icon {
  background: rgb(230 179 73 / 18%);
  border-color: rgb(230 179 73 / 36%);
  color: var(--color-gold-200);
}

.sys-layout__link-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sys-layout__link-text strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.02em;
}

.sys-layout__link-text small {
  font-size: 11px;
  opacity: 0.66;
  line-height: 1.4;
  margin-top: 2px;
}

.sys-layout__link-arrow {
  opacity: 0;
  transform: translateX(-4px);
  transition:
    opacity var(--duration-base) var(--easing-out),
    transform var(--duration-base) var(--easing-out);
}

.sys-layout__link:hover .sys-layout__link-arrow,
.sys-layout__link.router-link-active .sys-layout__link-arrow {
  opacity: 1;
  transform: translateX(0);
}

.sys-layout__link--danger {
  color: rgb(255 200 200 / 78%);
}

.sys-layout__link--danger.router-link-active {
  background:
    linear-gradient(120deg, rgb(211 47 47 / 28%) 0%, rgb(198 40 40 / 12%) 100%);
  border-color: rgb(211 47 47 / 50%);
  color: #fff;
}

.sys-layout__link--danger.router-link-active .sys-layout__link-bar {
  background: linear-gradient(180deg, #ff8a8a, #c62828);
  box-shadow: 0 0 12px rgb(198 40 40 / 56%);
}

.sys-layout__link--danger.router-link-active .sys-layout__link-icon {
  background: rgb(255 138 138 / 22%);
  border-color: rgb(255 138 138 / 40%);
  color: #ffd0d0;
}

.sys-layout__sidebar-foot {
  position: relative;
  margin-top: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid rgb(255 255 255 / 10%);
}

.sys-layout__sidebar-card {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: var(--space-3);
  padding: var(--space-3);
  background:
    linear-gradient(180deg, rgb(46 125 50 / 14%) 0%, rgb(46 125 50 / 4%) 100%);
  border: 1px solid rgb(46 125 50 / 22%);
  border-radius: var(--radius-md);
  align-items: center;
  box-shadow: 0 0 0 1px rgb(255 255 255 / 4%) inset;
}

.sys-layout__sidebar-card-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: rgb(46 125 50 / 24%);
  color: #b9f2bd;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.sys-layout__sidebar-card strong {
  display: block;
  font-size: 12px;
  font-weight: var(--font-weight-semibold);
  color: #fff;
}

.sys-layout__sidebar-card small {
  font-size: 10.5px;
  color: rgb(255 255 255 / 56%);
  line-height: 1.4;
}

.sys-layout__sidebar-stamp {
  font-family: var(--font-family-mono);
  font-size: 10px;
  letter-spacing: 0.32em;
  color: rgb(230 179 73 / 56%);
  text-align: center;
}

/* ── 主区头部 ─────────────────────────────────────────────────── */
.sys-layout__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sys-layout__header {
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

.sys-layout__crumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-family: var(--font-family-sans);
}

.sys-layout__crumb-icon {
  color: var(--color-brand-500);
}

.sys-layout__crumb strong {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.sys-layout__user {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.sys-layout__user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 11px;
  color: var(--color-text-secondary);
  letter-spacing: 0.06em;
}

.sys-layout__user-meta strong {
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  letter-spacing: 0;
}

.sys-layout__avatar {
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
  letter-spacing: 0;
  box-shadow:
    var(--shadow-glow-brand),
    inset 0 0 0 1px rgb(255 255 255 / 18%);
}

.sys-layout__avatar-dot {
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

.sys-layout__logout {
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

.sys-layout__logout:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
  box-shadow: 0 0 0 3px rgb(198 40 40 / 10%);
}

.sys-layout__content {
  flex: 1;
  padding: var(--space-6) clamp(var(--space-5), 3.5vw, var(--space-7));
  overflow: auto;
}

@media (width <= 1024px) {
  .sys-layout {
    grid-template-columns: 1fr;
  }

  .sys-layout__sidebar {
    display: none;
  }

  .sys-layout__content {
    padding: var(--space-4);
  }
}
</style>
