<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  warningsApi,
  WARNING_LEVEL_LABEL,
  WARNING_SCOPE_LABEL,
  WARNING_STATUS_LABEL,
  type WarningLevel,
  type WarningOut,
} from "@/api/warnings";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppErrorState,
  AppIcon,
  AppPageHeader,
  AppSkeleton,
  AppStatusTag,
} from "@/components";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const errored = ref(false);
const errorMsg = ref("");
const warning = ref<WarningOut | null>(null);

function warnLevelClass(
  level: WarningLevel,
): "info" | "warning" | "urgent" {
  if (level === 3) return "urgent";
  if (level === 2) return "warning";
  return "info";
}

function formatDateTime(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 16).replace("T", " ");
}

async function load(): Promise<void> {
  const warningId = String(route.params.warning_id ?? "");
  if (!warningId) {
    errored.value = true;
    errorMsg.value = "缺少预警编号";
    return;
  }
  loading.value = true;
  errored.value = false;
  errorMsg.value = "";
  try {
    warning.value = await warningsApi.getMine(warningId);
  } catch (e) {
    errored.value = true;
    errorMsg.value = e instanceof ApiError ? e.message : "加载失败";
    warning.value = null;
  } finally {
    loading.value = false;
  }
}

function goBack(): void {
  void router.push({ name: "warning-list" });
}

onMounted(load);
</script>

<template>
  <div class="warning-detail">
    <AppPageHeader badge="UC-07" title="预警详情" subtitle="阅读后将自动标记为已读">
      <template #actions>
        <AppButton variant="ghost" size="sm" @click="goBack">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
      </template>
    </AppPageHeader>

    <AppErrorState
      v-if="errored"
      title="加载失败"
      :hint="errorMsg || '请稍后重试'"
      retry-label="重新加载"
      @retry="load"
    />
    <template v-else>
      <AppCard v-if="loading" padding="lg">
        <AppSkeleton :rows="6" />
      </AppCard>
      <template v-else-if="warning">
        <AppCard
          :tone="warning.warning_level === 3 ? 'brand' : 'plain'"
          padding="lg"
          class="warning-detail__hero"
          :class="`warning-detail__hero--${warnLevelClass(warning.warning_level)}`"
        >
          <div class="warning-detail__hero-row">
            <AppStatusTag
              :status="'info'"
              :warn-level="warnLevelClass(warning.warning_level)"
              :text="`${WARNING_LEVEL_LABEL[warning.warning_level]}级`"
            />
            <span
              v-if="warning.status === 'OFFLINE'"
              class="warning-detail__offline"
            >已下线</span>
          </div>
          <h2 class="warning-detail__title">{{ warning.title }}</h2>
          <div class="warning-detail__meta">
            <span class="warning-detail__meta-cell">
              <AppIcon name="user" :size="13" />
              {{ warning.publisher_name || "—" }}
            </span>
            <span class="warning-detail__meta-cell">
              <AppIcon name="users" :size="13" />
              {{ WARNING_SCOPE_LABEL[warning.push_scope] ?? warning.push_scope }}
            </span>
            <span class="warning-detail__meta-cell">
              <AppIcon name="clock" :size="13" />
              {{ formatDateTime(warning.published_at) }}
            </span>
            <span v-if="warning.expires_at" class="warning-detail__meta-cell">
              <AppIcon name="calendar" :size="13" />
              失效于 {{ formatDateTime(warning.expires_at) }}
            </span>
          </div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>预警正文</h3>
              <small>请仔细阅读并按建议执行防范措施</small>
            </div>
          </template>
          <div class="warning-detail__content">{{ warning.content }}</div>
        </AppCard>

        <AppCard v-if="warning.appendix" padding="lg">
          <template #header>
            <div>
              <h3>追加说明</h3>
              <small>预警发布后补充的最新信息</small>
            </div>
          </template>
          <div class="warning-detail__content warning-detail__content--appendix">
            {{ warning.appendix }}
          </div>
        </AppCard>

        <AppCard v-if="warning.related_case_no" padding="md">
          <div class="warning-detail__related">
            <AppIcon name="file-text" :size="14" />
            <span>关联案件编号</span>
            <code>{{ warning.related_case_no }}</code>
          </div>
        </AppCard>

        <AppCard
          v-if="warning.status === 'OFFLINE'"
          padding="md"
        >
          <div class="warning-detail__offline-block">
            <AppIcon name="info" :size="14" />
            <div>
              <strong>该预警已于 {{ formatDateTime(warning.offline_at) }} 下线</strong>
              <p v-if="warning.offline_reason">{{ warning.offline_reason }}</p>
            </div>
          </div>
        </AppCard>

        <p class="warning-detail__footnote">
          <AppIcon name="info" :size="13" />
          状态：{{ WARNING_STATUS_LABEL[warning.status] ?? warning.status }}
        </p>
      </template>
    </template>
  </div>
</template>

<style scoped>
.warning-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.warning-detail__hero {
  position: relative;
  overflow: hidden;
}

.warning-detail__hero--info {
  background: linear-gradient(135deg, rgb(25 118 210 / 6%), rgb(25 118 210 / 2%));
  border-color: rgb(25 118 210 / 18%);
}

.warning-detail__hero--warning {
  background: linear-gradient(135deg, rgb(239 108 0 / 8%), rgb(239 108 0 / 2%));
  border-color: rgb(239 108 0 / 22%);
}

.warning-detail__hero--urgent {
  background: var(--gradient-brand);
  border-color: transparent;
  color: #fff;
  box-shadow:
    var(--shadow-glow-brand),
    inset 0 1px 0 rgb(255 255 255 / 10%);
}

.warning-detail__hero-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.warning-detail__title {
  margin: 0 0 var(--space-3);
  font-family: var(--font-family-serif);
  font-size: clamp(20px, 2.4vw, 30px);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.01em;
  line-height: 1.3;
  color: var(--color-text-strong);
}

.warning-detail__hero--urgent .warning-detail__title {
  color: #fff;
}

.warning-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-4);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.warning-detail__hero--urgent .warning-detail__meta {
  color: rgb(255 255 255 / 80%);
}

.warning-detail__meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.warning-detail__offline {
  font-size: 10.5px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-neutral-100);
  color: var(--color-neutral-600);
  letter-spacing: 0.04em;
}

.warning-detail__hero--urgent .warning-detail__offline {
  background: rgb(255 255 255 / 18%);
  color: #fff;
}

.warning-detail__content {
  font-size: var(--font-size-sm);
  line-height: 1.85;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}

.warning-detail__content--appendix {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(239 108 0 / 4%);
  border-left: 3px solid var(--color-warning);
}

.warning-detail__related {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.warning-detail__related code {
  font-family: var(--font-family-mono);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.warning-detail__offline-block {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  color: var(--color-text-secondary);
}

.warning-detail__offline-block strong {
  display: block;
  color: var(--color-text-strong);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.warning-detail__offline-block p {
  margin: 4px 0 0;
  font-size: var(--font-size-xs);
  line-height: 1.6;
}

.warning-detail__footnote {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}
</style>
