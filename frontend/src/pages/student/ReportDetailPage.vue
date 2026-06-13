<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { ReportDetailOut } from "@/api/reports";
import { STATUS_LABEL, STATUS_TYPE, reportsApi } from "@/api/reports";
import { AppButton, AppCard, AppIcon, AppPageHeader } from "@/components";

const route = useRoute();
const router = useRouter();
const caseId = String(route.params.case_id ?? "");

const loading = ref(true);
const detail = ref<ReportDetailOut | null>(null);
const error = ref("");

const STATUS_ICON: Record<string, string> = {
  PENDING: "clock",
  REVIEWING: "search",
  HANDLED: "check-circle",
  REJECTED: "circle-x",
  REPORTED: "shield-alert",
};

onMounted(async () => {
  try {
    if (!/^\d+$/.test(caseId)) {
      throw new Error("invalid-case-id");
    }
    detail.value = await reportsApi.getReport(caseId);
  } catch {
    error.value = "案件不存在或无权查看";
  } finally {
    loading.value = false;
  }
});

function formatDateTime(s: string) {
  if (!s) return "—";
  return new Date(s).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<template>
  <div class="report-detail">
    <div class="report-detail__back">
      <AppButton
        variant="ghost"
        size="sm"
        @click="router.back()"
      >
        <AppIcon
          name="arrow-left"
          :size="14"
        />
        返回
      </AppButton>
    </div>

    <div
      v-if="loading"
      class="report-detail__loading"
    >
      <AppIcon
        name="loader"
        :size="32"
        class="spin"
      />
      加载中…
    </div>

    <div
      v-else-if="error"
      class="report-detail__error"
    >
      <AppIcon
        name="alert-triangle"
        :size="32"
      />
      <p>{{ error }}</p>
    </div>

    <template v-else-if="detail">
      <AppPageHeader
        :title="detail.title"
        :subtitle="detail.case_no"
      />

      <div class="report-detail__layout">
        <!-- 左：详情 -->
        <div class="report-detail__left">
          <!-- 基本信息 -->
          <AppCard
            padding="lg"
            class="report-detail__info"
          >
            <template #header>
              <div class="report-detail__card-header">
                <h3>基本信息</h3>
                <span
                  class="report-detail__status"
                  :class="`report-detail__status--${STATUS_TYPE[detail.status]}`"
                >
                  <AppIcon
                    :name="(STATUS_ICON[detail.status] as never) || 'info'"
                    :size="14"
                  />
                  {{ STATUS_LABEL[detail.status] ?? detail.status }}
                </span>
              </div>
            </template>

            <dl class="report-detail__dl">
              <div class="report-detail__dl-row">
                <dt>案件编号</dt>
                <dd>
                  <code class="report-detail__case-no">{{ detail.case_no }}</code>
                </dd>
              </div>
              <div class="report-detail__dl-row">
                <dt>诈骗类型</dt>
                <dd>{{ detail.fraud_type_name ?? `#${detail.fraud_type_id}` }}</dd>
              </div>
              <div class="report-detail__dl-row">
                <dt>事发日期</dt>
                <dd>{{ detail.incident_date }}</dd>
              </div>
              <div
                v-if="detail.amount != null"
                class="report-detail__dl-row"
              >
                <dt>涉案金额</dt>
                <dd>¥ {{ detail.amount }}</dd>
              </div>
              <div
                v-if="detail.fraud_method"
                class="report-detail__dl-row"
              >
                <dt>诈骗手法</dt>
                <dd>{{ detail.fraud_method }}</dd>
              </div>
              <div class="report-detail__dl-row">
                <dt>上报方式</dt>
                <dd>
                  <span
                    v-if="detail.is_anonymous"
                    class="report-detail__anon-badge"
                  >
                    <AppIcon
                      name="eye-off"
                      :size="12"
                    />
                    匿名上报
                  </span>
                  <span v-else>实名上报</span>
                </dd>
              </div>
              <div class="report-detail__dl-row">
                <dt>证据图片</dt>
                <dd>{{ detail.evidence_count }} 张</dd>
              </div>
              <div class="report-detail__dl-row">
                <dt>提交时间</dt>
                <dd>{{ formatDateTime(detail.created_at) }}</dd>
              </div>
              <div
                v-if="detail.review_note"
                class="report-detail__dl-row"
              >
                <dt>审核意见</dt>
                <dd class="report-detail__review-note">{{ detail.review_note }}</dd>
              </div>
            </dl>
          </AppCard>

          <!-- 事件描述 -->
          <AppCard padding="lg">
            <template #header>
              <h3>事件描述</h3>
            </template>
            <p class="report-detail__description">{{ detail.description }}</p>
          </AppCard>
        </div>

        <!-- 右：时间线 -->
        <aside class="report-detail__timeline-col">
          <AppCard padding="lg">
            <template #header>
              <h3>处理时间线</h3>
            </template>

            <div
              v-if="detail.history.length === 0"
              class="report-detail__timeline-empty"
            >
              暂无处理记录
            </div>

            <ol
              v-else
              class="report-detail__timeline"
            >
              <li
                v-for="h in detail.history"
                :key="h.history_id"
                class="report-detail__timeline-item"
                :class="`report-detail__timeline-item--${STATUS_TYPE[h.to_status] ?? 'info'}`"
              >
                <div class="report-detail__timeline-dot" />
                <div class="report-detail__timeline-content">
                  <div class="report-detail__timeline-status">
                    <span
                      v-if="h.from_status"
                      class="report-detail__timeline-from"
                    >
                      {{ STATUS_LABEL[h.from_status] ?? h.from_status }}
                    </span>
                    <span
                      v-if="h.from_status"
                      class="report-detail__timeline-arrow"
                    >→</span>
                    <span class="report-detail__timeline-to">
                      {{ STATUS_LABEL[h.to_status] ?? h.to_status }}
                    </span>
                  </div>
                  <div
                    v-if="h.note"
                    class="report-detail__timeline-note"
                  >
                    {{ h.note }}
                  </div>
                  <div class="report-detail__timeline-time">
                    {{ formatDateTime(h.created_at) }}
                  </div>
                </div>
              </li>
            </ol>
          </AppCard>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.report-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.report-detail__back {
  margin-bottom: calc(-1 * var(--space-2));
}

.report-detail__loading,
.report-detail__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

.report-detail__layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--space-4);
  align-items: start;
}

@media (width <= 1024px) {
  .report-detail__layout {
    grid-template-columns: 1fr;
  }
}

.report-detail__left {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.report-detail__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.report-detail__card-header h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
}

.report-detail__status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.report-detail__status--info { background: rgb(21 101 192 / 10%); color: var(--color-info); }
.report-detail__status--warning { background: rgb(239 108 0 / 10%); color: var(--color-warning); }
.report-detail__status--success { background: rgb(46 125 50 / 10%); color: var(--color-success); }
.report-detail__status--danger { background: rgb(198 40 40 / 10%); color: var(--color-danger); }

.report-detail__dl {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.report-detail__dl-row {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: var(--space-3);
  align-items: baseline;
}

.report-detail__dl-row dt {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.report-detail__dl-row dd {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text);
}

.report-detail__case-no {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  color: var(--color-brand-700);
  background: var(--color-brand-50);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.report-detail__anon-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: rgb(134 38 51 / 8%);
  color: var(--color-brand-600);
}

.report-detail__review-note {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-soft);
  border-left: 2px solid var(--color-border-strong);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-style: italic;
  line-height: 1.6;
}

.report-detail__description {
  margin: 0;
  line-height: 1.8;
  font-size: var(--font-size-sm);
  color: var(--color-text);
  white-space: pre-wrap;
}

/* Timeline */
.report-detail__timeline-col {
  position: sticky;
  top: 80px;
}

.report-detail__timeline-empty {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-align: center;
  padding: var(--space-4);
}

.report-detail__timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}

.report-detail__timeline::before {
  content: "";
  position: absolute;
  left: 7px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--color-border);
}

.report-detail__timeline-item {
  position: relative;
  padding-left: 28px;
  padding-bottom: var(--space-4);
}

.report-detail__timeline-item:last-child {
  padding-bottom: 0;
}

.report-detail__timeline-dot {
  position: absolute;
  left: 0;
  top: 6px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-border);
  border: 2px solid var(--color-surface);
}

.report-detail__timeline-item--info .report-detail__timeline-dot { background: var(--color-info); }
.report-detail__timeline-item--warning .report-detail__timeline-dot { background: var(--color-warning); }
.report-detail__timeline-item--success .report-detail__timeline-dot { background: var(--color-success); }
.report-detail__timeline-item--danger .report-detail__timeline-dot { background: var(--color-danger); }

.report-detail__timeline-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-strong);
}

.report-detail__timeline-from {
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-normal);
  font-size: var(--font-size-xs);
}

.report-detail__timeline-arrow {
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.report-detail__timeline-note {
  margin-top: 4px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.report-detail__timeline-time {
  margin-top: 3px;
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.spin { animation: spin 1s linear infinite; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
