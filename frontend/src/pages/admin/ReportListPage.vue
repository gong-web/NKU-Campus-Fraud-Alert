<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { reportsApi, STATUS_LABEL } from "@/api/reports";
import type { AdminReportListItem, AdminReportListParams, FraudType } from "@/types/report";
import { AppButton, AppCard, AppEmpty, AppPageHeader, AppStatusTag } from "@/components";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const items = ref<AdminReportListItem[]>([]);
const total = ref(0);
const fraudTypes = ref<FraudType[]>([]);

const filters = reactive<{
  status: string[];
  fraud_type_id: number | null;
  date_from: string;
  date_to: string;
  amount_min: number | null;
  amount_max: number | null;
  keyword: string;
  page: number;
  size: number;
  sort: "created_at_desc" | "amount_desc";
}>({
  status: ["PENDING", "REVIEWING"],
  fraud_type_id: null,
  date_from: "",
  date_to: "",
  amount_min: null,
  amount_max: null,
  keyword: "",
  page: 1,
  size: 20,
  sort: "created_at_desc",
});

const dateRange = ref<[Date, Date] | null>(null);

const totalPages = computed<number>(() => Math.max(1, Math.ceil(total.value / filters.size)));

function statusTone(status: string): "neutral" | "info" | "success" | "danger" | "warning" {
  if (status === "PENDING") return "neutral";
  if (status === "REVIEWING") return "info";
  if (status === "HANDLED") return "success";
  if (status === "REJECTED") return "danger";
  return "warning";
}

function syncFromRoute(): void {
  const q = route.query;
  filters.status = typeof q.status === "string" ? q.status.split(",").filter(Boolean) : ["PENDING", "REVIEWING"];
  filters.fraud_type_id = typeof q.fraud_type_id === "string" ? Number(q.fraud_type_id) : null;
  filters.date_from = typeof q.date_from === "string" ? q.date_from : "";
  filters.date_to = typeof q.date_to === "string" ? q.date_to : "";
  filters.amount_min = typeof q.amount_min === "string" ? Number(q.amount_min) : null;
  filters.amount_max = typeof q.amount_max === "string" ? Number(q.amount_max) : null;
  filters.keyword = typeof q.keyword === "string" ? q.keyword : "";
  filters.page = typeof q.page === "string" ? Number(q.page) : 1;
  filters.size = typeof q.size === "string" ? Number(q.size) : 20;
  filters.sort = q.sort === "amount_desc" ? "amount_desc" : "created_at_desc";
  dateRange.value = filters.date_from && filters.date_to ? [new Date(filters.date_from), new Date(filters.date_to)] : null;
}

async function syncRouteAndLoad(): Promise<void> {
  const query = {
    status: filters.status.join(","),
    fraud_type_id: filters.fraud_type_id != null ? String(filters.fraud_type_id) : undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    amount_min: filters.amount_min != null ? String(filters.amount_min) : undefined,
    amount_max: filters.amount_max != null ? String(filters.amount_max) : undefined,
    keyword: filters.keyword || undefined,
    page: String(filters.page),
    size: String(filters.size),
    sort: filters.sort,
  };
  await router.replace({ query });
  await load();
}

async function load(): Promise<void> {
  loading.value = true;
  try {
    const params: AdminReportListParams = {
      status: filters.status,
      page: filters.page,
      size: filters.size,
      sort: filters.sort,
      ...(filters.fraud_type_id != null ? { fraud_type_id: filters.fraud_type_id } : {}),
      ...(filters.date_from ? { date_from: filters.date_from } : {}),
      ...(filters.date_to ? { date_to: filters.date_to } : {}),
      ...(filters.amount_min != null ? { amount_min: filters.amount_min } : {}),
      ...(filters.amount_max != null ? { amount_max: filters.amount_max } : {}),
      ...(filters.keyword ? { keyword: filters.keyword } : {}),
    };
    const result = await reportsApi.listAdminReports(params);
    items.value = result.items;
    total.value = result.total;
  } finally {
    loading.value = false;
  }
}

async function loadFraudTypes(): Promise<void> {
  fraudTypes.value = await reportsApi.listFraudTypes();
}

async function applyFilters(): Promise<void> {
  filters.page = 1;
  if (dateRange.value) {
    filters.date_from = dateRange.value[0].toISOString().slice(0, 10);
    filters.date_to = dateRange.value[1].toISOString().slice(0, 10);
  } else {
    filters.date_from = "";
    filters.date_to = "";
  }
  await syncRouteAndLoad();
}

async function resetFilters(): Promise<void> {
  filters.status = ["PENDING", "REVIEWING"];
  filters.fraud_type_id = null;
  filters.date_from = "";
  filters.date_to = "";
  filters.amount_min = null;
  filters.amount_max = null;
  filters.keyword = "";
  filters.page = 1;
  filters.sort = "created_at_desc";
  dateRange.value = null;
  await syncRouteAndLoad();
}

async function openDetail(caseId: string): Promise<void> {
  await router.push({ name: "admin-report-detail", params: { case_id: caseId } });
}

watch(() => route.fullPath, syncFromRoute);

onMounted(async () => {
  syncFromRoute();
  await Promise.all([loadFraudTypes(), load()]);
});
</script>

<template>
  <div class="admin-report-list">
    <AppPageHeader title="审核队列" :subtitle="`当前共 ${total} 条待处理事件`" />

    <AppCard padding="md">
      <div class="admin-report-list__filters">
        <div class="admin-report-list__filters-grid">
          <label class="field">
            <span>状态</span>
            <ElSelect v-model="filters.status" multiple collapse-tags collapse-tags-tooltip placeholder="选择状态">
              <ElOption label="待审核" value="PENDING" />
              <ElOption label="审核中" value="REVIEWING" />
              <ElOption label="已处理" value="HANDLED" />
              <ElOption label="已驳回" value="REJECTED" />
              <ElOption label="已转报警" value="REPORTED" />
            </ElSelect>
          </label>
          <label class="field">
            <span>诈骗类型</span>
            <ElSelect v-model="filters.fraud_type_id" clearable placeholder="全部类型">
              <ElOption v-for="item in fraudTypes" :key="item.type_id" :label="item.type_name" :value="item.type_id" />
            </ElSelect>
          </label>
          <label class="field">
            <span>日期范围</span>
            <ElDatePicker v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
          </label>
          <label class="field">
            <span>金额下限</span>
            <ElInputNumber v-model="filters.amount_min" :min="0" :precision="2" :controls="false" />
          </label>
          <label class="field">
            <span>金额上限</span>
            <ElInputNumber v-model="filters.amount_max" :min="0" :precision="2" :controls="false" />
          </label>
          <label class="field field--wide">
            <span>关键词</span>
            <ElInput v-model="filters.keyword" placeholder="搜索案件标题" clearable @keyup.enter="applyFilters" />
          </label>
        </div>
        <div class="admin-report-list__filter-actions">
          <AppButton variant="ghost" @click="resetFilters">重置</AppButton>
          <AppButton variant="primary" @click="applyFilters">筛选</AppButton>
        </div>
      </div>
    </AppCard>

    <AppCard padding="none">
      <div v-if="loading" class="admin-report-list__loading">加载中...</div>
      <div v-else-if="items.length === 0" class="admin-report-list__empty">
        <AppEmpty title="暂无待审核事件" illustration="search" />
      </div>
      <div v-else class="admin-report-list__table-wrap">
        <table class="admin-report-list__table">
          <thead>
            <tr>
              <th>案件编号</th>
              <th>标题</th>
              <th>诈骗类型</th>
              <th>金额</th>
              <th>状态</th>
              <th>提交时间</th>
              <th>证据数</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.case_id">
              <td><code>{{ item.case_no }}</code></td>
              <td class="title-cell">{{ item.title }}</td>
              <td>{{ item.fraud_type_name || "—" }}</td>
              <td>{{ item.amount ?? "—" }}</td>
              <td>
                <AppStatusTag :status="statusTone(item.status)" :text="STATUS_LABEL[item.status] || item.status" />
              </td>
              <td>{{ item.created_at.slice(0, 16).replace("T", " ") }}</td>
              <td>{{ item.evidence_count }}</td>
              <td>
                <AppButton variant="ghost" size="sm" @click="openDetail(item.case_id)">查看处理</AppButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </AppCard>

    <div class="admin-report-list__pager">
      <AppButton variant="ghost" size="sm" :disabled="filters.page <= 1" @click="filters.page -= 1; syncRouteAndLoad()">上一页</AppButton>
      <span>第 {{ filters.page }} / {{ totalPages }} 页</span>
      <AppButton variant="ghost" size="sm" :disabled="filters.page >= totalPages" @click="filters.page += 1; syncRouteAndLoad()">下一页</AppButton>
    </div>
  </div>
</template>

<style scoped>
.admin-report-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-report-list__filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-report-list__filters-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field span {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.field--wide {
  grid-column: span 2;
}

.admin-report-list__filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

.admin-report-list__loading,
.admin-report-list__empty {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.admin-report-list__table-wrap {
  overflow: auto;
}

.admin-report-list__table {
  width: 100%;
  border-collapse: collapse;
}

.admin-report-list__table th,
.admin-report-list__table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  white-space: nowrap;
}

.admin-report-list__table th {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.title-cell {
  white-space: normal;
  min-width: 220px;
  color: var(--color-text-strong);
}

.admin-report-list__pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-3);
}

@media (width <= 1024px) {
  .admin-report-list__filters-grid {
    grid-template-columns: 1fr;
  }

  .field--wide {
    grid-column: span 1;
  }
}
</style>
