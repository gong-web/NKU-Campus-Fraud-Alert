<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { reportsApi, STATUS_LABEL } from "@/api/reports";
import type { DashboardSummaryOut } from "@/types/report";
import { useAuthStore } from "@/stores/auth";
import { AppButton, AppCard, AppEmpty, AppPageHeader, AppStatCard, AppStatusTag } from "@/components";

const auth = useAuthStore();
const router = useRouter();
const loading = ref(false);
const summary = ref<DashboardSummaryOut | null>(null);

const greeting = computed<string>(() => {
  const hour = new Date().getHours();
  if (hour < 5) return "凌晨好";
  if (hour < 12) return "早上好";
  if (hour < 14) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

const trendPoints = computed(() => summary.value?.trend_7days ?? []);

const maxTrendValue = computed<number>(() => {
  return Math.max(
    1,
    ...trendPoints.value.flatMap((item) => [item.submitted, item.handled]),
  );
});

const submittedPolyline = computed<string>(() => {
  if (trendPoints.value.length === 0) return "";
  return trendPoints.value
    .map((item, index) => {
      const x = (index / Math.max(trendPoints.value.length - 1, 1)) * 100;
      const y = 60 - (item.submitted / maxTrendValue.value) * 52;
      return `${x},${y}`;
    })
    .join(" ");
});

const handledPolyline = computed<string>(() => {
  if (trendPoints.value.length === 0) return "";
  return trendPoints.value
    .map((item, index) => {
      const x = (index / Math.max(trendPoints.value.length - 1, 1)) * 100;
      const y = 60 - (item.handled / maxTrendValue.value) * 52;
      return `${x},${y}`;
    })
    .join(" ");
});

const statCards = computed(() => {
  const data = summary.value;
  return [
    {
      label: "待办案件",
      value: data?.pending_count ?? "—",
      hint: data && data.pending_count > 10 ? "待办较多，请优先处理" : undefined,
      icon: "clipboard-list",
      tone: data && data.pending_count > 10 ? "danger" : "brand",
    },
    {
      label: "审核中",
      value: data?.reviewing_count ?? "—",
      hint: "",
      icon: "activity",
      tone: "info",
    },
    {
      label: "今日已处理",
      value: data?.today_handled ?? "—",
      hint: "",
      icon: "check-circle",
      tone: "brand",
    },
    {
      label: "今日驳回 / 转报",
      value: data ? `${data.today_rejected} / ${data.today_reported}` : "—",
      hint: "",
      icon: "shield-alert",
      tone: "warning",
    },
  ] as const;
});

async function load(): Promise<void> {
  loading.value = true;
  try {
    summary.value = await reportsApi.getAdminDashboardSummary();
  } finally {
    loading.value = false;
  }
}

function openQueue(): void {
  void router.push({ name: "admin-reports" });
}

onMounted(load);
</script>

<template>
  <div class="admin-dash">
    <AppPageHeader
      :title="`${greeting}，${auth.me?.real_name ?? '审核员'}`"
    >
      <template #actions>
        <AppButton variant="primary" size="sm" @click="openQueue">
          审核队列
        </AppButton>
      </template>
    </AppPageHeader>
    <section class="admin-dash__tracks">
      <AppStatCard v-for="item in statCards" :key="item.label" :label="item.label" :value="item.value" :hint="item.hint ?? ''" :icon="item.icon" :tone="item.tone" />
    </section>
    <section class="admin-dash__grid">
      <AppCard padding="md" class="admin-dash__panel">
        <template #header>
          <h3>近 7 日趋势</h3>
        </template>
        <div v-if="loading" class="admin-dash__loading">
          载入中...
        </div>
        <div v-else-if="trendPoints.length === 0" class="admin-dash__empty-wrap">
          <AppEmpty title="暂无趋势数据" />
        </div>
        <div v-else class="admin-dash__chart-wrap">
          <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="admin-dash__chart">
            <polyline class="admin-dash__chart-line admin-dash__chart-line--submitted" :points="submittedPolyline" />
            <polyline class="admin-dash__chart-line admin-dash__chart-line--handled" :points="handledPolyline" />
          </svg>
          <div class="admin-dash__chart-legend">
            <span><i class="legend-dot submitted" />提交</span>
            <span><i class="legend-dot handled" />已处理</span>
          </div>
          <div class="admin-dash__chart-axis">
            <span v-for="point in trendPoints" :key="point.date">{{ point.date.slice(5) }}</span>
          </div>
        </div>
      </AppCard>

      <AppCard padding="md" class="admin-dash__panel">
        <template #header>
          <h3>最近处理</h3>
        </template>
        <div v-if="loading" class="admin-dash__loading">
          载入中...
        </div>
        <div v-else-if="!summary?.my_recent_actions.length" class="admin-dash__empty-wrap">
          <AppEmpty title="暂无处理记录" />
        </div>
        <div v-else class="admin-dash__recent-list">
          <article v-for="item in summary?.my_recent_actions" :key="`${item.case_id}-${item.created_at}`" class="admin-dash__recent-item">
            <div>
              <strong>{{ item.case_no }}</strong>
              <p>{{ item.note || "已执行审核动作" }}</p>
            </div>
            <div class="admin-dash__recent-meta">
              <AppStatusTag :status="item.to_status === 'HANDLED' ? 'success' : item.to_status === 'REJECTED' ? 'danger' : item.to_status === 'REPORTED' ? 'warning' : 'info'" :text="STATUS_LABEL[item.to_status] || item.to_status" />
              <small>{{ item.created_at.slice(0, 16).replace('T', ' ') }}</small>
            </div>
          </article>
        </div>
      </AppCard>
    </section>
  </div>
</template>

<style scoped>
.admin-dash {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ── 待办计数 ─────────────────────────────────────────────────── */
.admin-dash__tracks {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}

.admin-dash__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

@media (width <= 1024px) {
  .admin-dash__grid {
    grid-template-columns: 1fr;
  }
}

.admin-dash__panel h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.admin-dash__panel small {
  display: block;
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-dash__loading,
.admin-dash__empty-wrap {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.admin-dash__chart-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.admin-dash__chart {
  width: 100%;
  height: 220px;
  border-radius: var(--radius-md);
  background:
    linear-gradient(to top, rgb(134 38 51 / 3%), transparent 70%),
    repeating-linear-gradient(to top, var(--color-border) 0 1px, transparent 1px 44px);
}

.admin-dash__chart-line {
  fill: none;
  stroke-width: 2.6;
  vector-effect: non-scaling-stroke;
}

.admin-dash__chart-line--submitted {
  stroke: var(--color-brand-500);
}

.admin-dash__chart-line--handled {
  stroke: var(--color-success);
}

.admin-dash__chart-legend,
.admin-dash__chart-axis {
  display: flex;
  justify-content: space-between;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  margin-right: 6px;
}

.legend-dot.submitted {
  background: var(--color-brand-500);
}

.legend-dot.handled {
  background: var(--color-success);
}

.admin-dash__recent-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.admin-dash__recent-item {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-soft);
}

.admin-dash__recent-item strong {
  display: block;
  color: var(--color-text-strong);
}

.admin-dash__recent-item p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.admin-dash__recent-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

@media (width <= 768px) {
  .admin-dash__recent-item {
    flex-direction: column;
  }

  .admin-dash__recent-meta {
    align-items: flex-start;
  }
}
</style>
