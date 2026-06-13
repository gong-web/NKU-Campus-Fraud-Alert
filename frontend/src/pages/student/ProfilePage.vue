<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { AppButton, AppCard, AppIcon, AppPageHeader } from "@/components";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const initial = computed(() => {
  const name = auth.me?.real_name || "?";
  return Array.from(name)[0] ?? "?";
});

const roleLabel = computed(() => {
  const r = auth.me?.role_code;
  if (r === "STUDENT") return "学生";
  if (r === "REVIEWER") return "审核员";
  if (r === "SYS_ADMIN") return "系统管理员";
  return r ?? "—";
});
</script>

<template>
  <div class="profile-page">
    <AppPageHeader title="我的信息" />

    <div class="profile-page__layout">
      <!-- 左侧栏：名片 + 隐私说明 -->
      <aside class="profile-page__sidebar">
        <AppCard padding="lg" class="profile-page__card">
          <div class="profile-page__avatar">{{ initial }}</div>
          <h2 class="profile-page__name">{{ auth.me?.real_name ?? '未知' }}</h2>
          <p class="profile-page__meta">
            <span class="profile-page__role-badge">{{ roleLabel }}</span>
            <span class="profile-page__account">{{ auth.me?.cas_account }}</span>
          </p>
        </AppCard>

      </aside>

      <!-- 右侧：快捷入口网格 -->
      <div class="profile-page__quick">
        <AppCard padding="md" class="profile-page__quick-item" @click="router.push({ name: 'report-form' })">
          <div class="profile-page__quick-icon-wrap">
            <AppIcon name="siren" :size="24" />
          </div>
          <div class="profile-page__quick-body">
            <h3>我要上报</h3>
            <p>提交诈骗事件上报</p>
          </div>
          <AppIcon name="arrow-right" :size="16" class="profile-page__quick-arrow" />
        </AppCard>

        <AppCard padding="md" class="profile-page__quick-item" @click="router.push({ name: 'my-reports' })">
          <div class="profile-page__quick-icon-wrap">
            <AppIcon name="clipboard-list" :size="24" />
          </div>
          <div class="profile-page__quick-body">
            <h3>我的上报</h3>
            <p>查看历史上报与处理进展</p>
          </div>
          <AppIcon name="arrow-right" :size="16" class="profile-page__quick-arrow" />
        </AppCard>

        <AppCard padding="md" class="profile-page__quick-item" @click="router.push({ name: 'drafts' })">
          <div class="profile-page__quick-icon-wrap">
            <AppIcon name="file-text" :size="24" />
          </div>
          <div class="profile-page__quick-body">
            <h3>草稿箱</h3>
            <p>继续编辑未完成的上报</p>
          </div>
          <AppIcon name="arrow-right" :size="16" class="profile-page__quick-arrow" />
        </AppCard>

      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ── 两栏布局 ── */
.profile-page__layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: var(--space-4);
  align-items: start;
}

@media (max-width: 768px) {
  .profile-page__layout {
    grid-template-columns: 1fr;
  }
}

/* ── 左侧栏 ── */
.profile-page__sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  position: sticky;
  top: var(--space-4);
}

@media (max-width: 768px) {
  .profile-page__sidebar {
    position: static;
  }
}

/* ── 名片 ── */
.profile-page__card {
  text-align: center;
  color: #fff;
}

.profile-page__avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgb(255 255 255 / 20%);
  border: 2px solid rgb(255 255 255 / 40%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-family-serif);
  font-size: 28px;
  font-weight: var(--font-weight-bold);
  margin: 0 auto var(--space-3);
}

.profile-page__name {
  margin: 0 0 var(--space-2);
  font-family: var(--font-family-serif);
  font-size: clamp(18px, 2vw, 24px);
  font-weight: var(--font-weight-bold);
}

.profile-page__meta {
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.profile-page__role-badge {
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: rgb(255 255 255 / 20%);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.04em;
}

.profile-page__account {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  color: rgb(255 255 255 / 75%);
}

/* ── 隐私说明 ── */
.profile-page__tip-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.profile-page__tip-header svg {
  color: var(--color-success);
}

.profile-page__tips {
  margin: 0;
  padding: 0 0 0 var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.profile-page__tips li {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.65;
}

/* ── 快捷入口网格 ── */
.profile-page__quick {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
  align-content: start;
}

@media (max-width: 640px) {
  .profile-page__quick {
    grid-template-columns: 1fr;
  }
}

.profile-page__quick-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
  transition:
    border-color var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    transform var(--duration-base) var(--easing-out);
}

.profile-page__quick-item:hover {
  border-color: var(--color-brand-400);
  box-shadow: 0 4px 12px rgb(0 0 0 / 6%);
  transform: translateY(-2px);
}

/* 图标容器 - 完美居中 */
.profile-page__quick-icon-wrap {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-brand-50, rgb(var(--color-brand-rgb, 79 70 229) / 8%));
  color: var(--color-brand-600);
  transition: background var(--duration-base) var(--easing-out);
}

.profile-page__quick-item:hover .profile-page__quick-icon-wrap {
  background: var(--color-brand-100, rgb(var(--color-brand-rgb, 79 70 229) / 15%));
}

/* 内容区域 */
.profile-page__quick-body {
  flex: 1;
}

.profile-page__quick-body h3 {
  margin: 0 0 2px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.profile-page__quick-body p {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

/* 箭头图标 - 垂直居中 */
.profile-page__quick-arrow {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
  transition:
    transform var(--duration-base) var(--easing-out),
    color var(--duration-base) var(--easing-out);
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-page__quick-item:hover .profile-page__quick-arrow {
  transform: translateX(3px);
  color: var(--color-brand-600);
}
</style>