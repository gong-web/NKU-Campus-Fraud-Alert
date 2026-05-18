<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { AppButton, AppCard, AppIcon } from "@/components";

const route = useRoute();
const router = useRouter();

const caseNo = computed(() => String(route.query.case_no ?? ""));
const caseId = computed(() => Number(route.query.case_id ?? 0));
</script>

<template>
  <div class="success-page">
    <AppCard
      padding="lg"
      class="success-page__card"
    >
      <div class="success-page__icon">
        <AppIcon
          name="check-circle"
          :size="64"
        />
      </div>

      <h1 class="success-page__title">上报成功</h1>
      <p class="success-page__subtitle">您的上报已进入审核队列，审核员将在 24 小时内处理。</p>

      <div class="success-page__case-no">
        <span class="success-page__case-label">案件编号</span>
        <code class="success-page__case-code">{{ caseNo }}</code>
      </div>

      <p class="success-page__tip">
        <AppIcon
          name="bell"
          :size="14"
        />
        状态变更时系统会发送站内通知，请注意查收。
      </p>

      <div class="success-page__actions">
        <AppButton
          variant="ghost"
          @click="router.push({ name: 'student-home' })"
        >
          返回首页
        </AppButton>
        <AppButton
          variant="primary"
          @click="router.push({ name: 'my-reports' })"
        >
          <AppIcon
            name="clipboard-list"
            :size="16"
          />
          查看我的上报
        </AppButton>
        <AppButton
          v-if="caseId > 0"
          variant="ghost"
          @click="router.push({ name: 'report-detail', params: { case_id: caseId } })"
        >
          <AppIcon
            name="eye"
            :size="16"
          />
          查看案件详情
        </AppButton>
      </div>
    </AppCard>
  </div>
</template>

<style scoped>
.success-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.success-page__card {
  max-width: 480px;
  width: 100%;
  text-align: center;
}

.success-page__icon {
  color: var(--color-success);
  margin-bottom: var(--space-4);
}

.success-page__title {
  margin: 0 0 var(--space-2);
  font-family: var(--font-family-serif);
  font-size: clamp(24px, 3vw, 32px);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-strong);
}

.success-page__subtitle {
  margin: 0 0 var(--space-5);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.success-page__case-no {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  background: var(--color-brand-50);
  border: 1px solid rgb(134 38 51 / 16%);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
}

.success-page__case-label {
  font-size: var(--font-size-xs);
  color: var(--color-brand-700);
  font-weight: var(--font-weight-medium);
}

.success-page__case-code {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--color-brand-700);
  letter-spacing: 0.08em;
}

.success-page__tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-5);
}

.success-page__actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  flex-wrap: wrap;
}
</style>
