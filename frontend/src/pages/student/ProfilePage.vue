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
    <AppPageHeader
      badge="个人中心"
      title="我的信息"
      subtitle="查看个人基本信息，管理上报记录与草稿。"
    />

    <div class="profile-page__layout">
      <!-- 用户名片 -->
      <AppCard
        tone="brand"
        padding="lg"
        class="profile-page__card"
      >
        <div class="profile-page__avatar">
          {{ initial }}
        </div>
        <h2 class="profile-page__name">{{ auth.me?.real_name ?? '未知' }}</h2>
        <p class="profile-page__meta">
          <span class="profile-page__role-badge">{{ roleLabel }}</span>
          <span class="profile-page__account">{{ auth.me?.cas_account }}</span>
        </p>
      </AppCard>

      <!-- 快捷入口 -->
      <div class="profile-page__quick">
        <AppCard
          padding="md"
          class="profile-page__quick-item"
          @click="router.push({ name: 'report-form' })"
        >
          <AppIcon
            name="siren"
            :size="28"
            class="profile-page__quick-icon"
          />
          <div>
            <h3>我要上报</h3>
            <p>提交诈骗事件上报</p>
          </div>
          <AppIcon
            name="arrow-right"
            :size="16"
            class="profile-page__quick-arrow"
          />
        </AppCard>

        <AppCard
          padding="md"
          class="profile-page__quick-item"
          @click="router.push({ name: 'my-reports' })"
        >
          <AppIcon
            name="clipboard-list"
            :size="28"
            class="profile-page__quick-icon"
          />
          <div>
            <h3>我的上报</h3>
            <p>查看历史上报与处理进展</p>
          </div>
          <AppIcon
            name="arrow-right"
            :size="16"
            class="profile-page__quick-arrow"
          />
        </AppCard>

        <AppCard
          padding="md"
          class="profile-page__quick-item"
          @click="router.push({ name: 'drafts' })"
        >
          <AppIcon
            name="file-text"
            :size="28"
            class="profile-page__quick-icon"
          />
          <div>
            <h3>草稿箱</h3>
            <p>继续编辑未完成的上报</p>
          </div>
          <AppIcon
            name="arrow-right"
            :size="16"
            class="profile-page__quick-arrow"
          />
        </AppCard>
      </div>

      <!-- 安全提示 -->
      <AppCard padding="md">
        <template #header>
          <div class="profile-page__tip-header">
            <AppIcon
              name="shield-check"
              :size="16"
            />
            隐私保护说明
          </div>
        </template>
        <ul class="profile-page__tips">
          <li>您的个人信息（姓名、学号、联系方式）全程加密存储</li>
          <li>匿名上报时，真实身份仅在司法授权的情况下才能解密</li>
          <li>所有管理员操作均记录审计日志，可追溯</li>
          <li>平台不会主动向第三方共享您的信息</li>
        </ul>
      </AppCard>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.profile-page__layout {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 600px;
}

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
  font-size: clamp(20px, 2.5vw, 28px);
  font-weight: var(--font-weight-bold);
}

.profile-page__meta {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
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
  color: rgb(255 255 255 / 80%);
}

/* Quick links */
.profile-page__quick {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.profile-page__quick-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-out);
}

.profile-page__quick-item:hover {
  border-color: var(--color-brand-400);
  transform: translateX(3px);
}

.profile-page__quick-icon {
  color: var(--color-brand-600);
  flex-shrink: 0;
}

.profile-page__quick-item h3 {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.profile-page__quick-item p {
  margin: 2px 0 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.profile-page__quick-arrow {
  margin-left: auto;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  transition: transform var(--duration-base);
}

.profile-page__quick-item:hover .profile-page__quick-arrow {
  transform: translateX(3px);
  color: var(--color-brand-600);
}

/* Tips */
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
  line-height: 1.6;
}
</style>
