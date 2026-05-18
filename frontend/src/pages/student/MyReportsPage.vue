<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import type { ReportOut } from "@/api/reports";
import { STATUS_LABEL, STATUS_TYPE, reportsApi } from "@/api/reports";
import { AppButton, AppCard, AppIcon, AppPageHeader } from "@/components";

const router = useRouter();

const loading = ref(false);
const reports = ref<ReportOut[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(20);
const statusFilter = ref<string>("");

const STATUS_OPTIONS = [
  { value: "", label: "全部" },
  { value: "PENDING", label: "待审核" },
  { value: "REVIEWING", label: "审核中" },
  { value: "HANDLED", label: "已处理" },
  { value: "REJECTED", label: "已驳回" },
  { value: "REPORTED", label: "已转报警" },
];

async function load() {
  loading.value = true;
  try {
    const result = await reportsApi.listMyReports({
      ...(statusFilter.value ? { status: statusFilter.value } : {}),
      page: page.value,
      size: size.value,
    });
    reports.value = result.items;
    total.value = result.total;
  } catch {
    reports.value = [];
  } finally {
    loading.value = false;
  }
}

function formatDate(d: string) {
  return d ? d.slice(0, 10) : "—";
}

onMounted(load);
</script>

<template>
  <div class="my-reports">
    <AppPageHeader
      badge="UC-02"
      title="我的上报记录"
      :subtitle="`共 ${total} 条上报`"
    />

    <!-- 筛选栏 -->
    <div class="my-reports__filter">
      <button
        v-for="opt in STATUS_OPTIONS"
        :key="opt.value"
        class="my-reports__filter-btn"
        :class="{ active: statusFilter === opt.value }"
        type="button"
        @click="statusFilter = opt.value; page = 1; load()"
      >
        {{ opt.label }}
      </button>
      <AppButton
        variant="primary"
        size="sm"
        @click="router.push({ name: 'report-form' })"
      >
        <AppIcon
          name="plus"
          :size="14"
        />
        新建上报
      </AppButton>
    </div>

    <!-- 列表 -->
    <AppCard padding="none">
      <div
        v-if="loading"
        class="my-reports__loading"
      >
        <AppIcon
          name="loader"
          :size="24"
          class="spin"
        />
        加载中…
      </div>

      <div
        v-else-if="reports.length === 0"
        class="my-reports__empty"
      >
        <AppIcon
          name="inbox"
          :size="40"
        />
        <p>暂无上报记录</p>
        <AppButton
          variant="primary"
          @click="router.push({ name: 'report-form' })"
        >
          立即上报
        </AppButton>
      </div>

      <table
        v-else
        class="my-reports__table"
      >
        <thead>
          <tr>
            <th>案件编号</th>
            <th>标题</th>
            <th>类型</th>
            <th>事发日期</th>
            <th>状态</th>
            <th>提交时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in reports"
            :key="r.case_id"
            class="my-reports__row"
            @click="router.push({ name: 'report-detail', params: { case_id: r.case_id } })"
          >
            <td>
              <code class="my-reports__case-no">{{ r.case_no }}</code>
            </td>
            <td class="my-reports__title">{{ r.title }}</td>
            <td>{{ r.fraud_type_name ?? '—' }}</td>
            <td>{{ r.incident_date }}</td>
            <td>
              <span
                class="my-reports__status-badge"
                :class="`my-reports__status-badge--${STATUS_TYPE[r.status] ?? 'info'}`"
              >
                {{ STATUS_LABEL[r.status] ?? r.status }}
              </span>
            </td>
            <td>{{ formatDate(r.created_at) }}</td>
            <td @click.stop>
              <AppButton
                variant="ghost"
                size="sm"
                @click="router.push({ name: 'report-detail', params: { case_id: r.case_id } })"
              >
                <AppIcon
                  name="eye"
                  :size="14"
                />
                查看
              </AppButton>
            </td>
          </tr>
        </tbody>
      </table>
    </AppCard>

    <!-- 分页 -->
    <div
      v-if="total > size"
      class="my-reports__pagination"
    >
      <AppButton
        variant="ghost"
        size="sm"
        :disabled="page <= 1"
        @click="page--; load()"
      >
        上一页
      </AppButton>
      <span>{{ page }} / {{ Math.ceil(total / size) }}</span>
      <AppButton
        variant="ghost"
        size="sm"
        :disabled="page >= Math.ceil(total / size)"
        @click="page++; load()"
      >
        下一页
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.my-reports {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.my-reports__filter {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.my-reports__filter-btn {
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-out);
  font-family: inherit;
}

.my-reports__filter-btn:hover,
.my-reports__filter-btn.active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
}

.my-reports__loading,
.my-reports__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.my-reports__empty svg {
  color: var(--color-border-strong);
}

.my-reports__table {
  width: 100%;
  border-collapse: collapse;
}

.my-reports__table th {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.my-reports__row {
  cursor: pointer;
  transition: background var(--duration-base);
}

.my-reports__row:hover {
  background: var(--color-bg-soft);
}

.my-reports__row td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
}

.my-reports__case-no {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  color: var(--color-brand-700);
  background: var(--color-brand-50);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.my-reports__title {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: var(--font-weight-medium);
}

.my-reports__status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: var(--font-weight-medium);
}

.my-reports__status-badge--info {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
}

.my-reports__status-badge--warning {
  background: rgb(239 108 0 / 10%);
  color: var(--color-warning);
}

.my-reports__status-badge--success {
  background: rgb(46 125 50 / 10%);
  color: var(--color-success);
}

.my-reports__status-badge--danger {
  background: rgb(198 40 40 / 10%);
  color: var(--color-danger);
}

.my-reports__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
