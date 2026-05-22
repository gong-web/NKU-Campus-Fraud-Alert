<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  warningsApi,
  WARNING_LEVEL_LABEL,
  WARNING_SCOPE_LABEL,
  WARNING_STATUS_LABEL,
  type WarningAdminListParams,
  type WarningLevel,
  type WarningListItem,
  type WarningStatus,
} from "@/api/warnings";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppEmpty,
  AppErrorState,
  AppIcon,
  AppPageHeader,
  AppStatusTag,
} from "@/components";

const router = useRouter();

const loading = ref(false);
const errored = ref(false);
const items = ref<WarningListItem[]>([]);
const total = ref(0);

const page = ref(1);
const size = ref(15);
const keyword = ref("");
const statusFilter = ref<WarningStatus | "">("");
const levelFilter = ref<WarningLevel | 0>(0);

const STATUS_OPTIONS: ReadonlyArray<{ value: WarningStatus | ""; label: string }> = [
  { value: "", label: "全部" },
  { value: "ONLINE", label: "上线中" },
  { value: "OFFLINE", label: "已下线" },
];

const LEVEL_OPTIONS: ReadonlyArray<{ value: WarningLevel | 0; label: string }> = [
  { value: 0, label: "全部级别" },
  { value: 1, label: "提示" },
  { value: 2, label: "警告" },
  { value: 3, label: "紧急" },
];

const totalPages = computed<number>(() =>
  Math.max(1, Math.ceil(total.value / size.value)),
);

function warnLevelClass(level: WarningLevel): "info" | "warning" | "urgent" {
  if (level === 3) return "urgent";
  if (level === 2) return "warning";
  return "info";
}

function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 16).replace("T", " ");
}

async function load(): Promise<void> {
  loading.value = true;
  errored.value = false;
  try {
    const params: WarningAdminListParams = {
      page: page.value,
      size: size.value,
      ...(keyword.value ? { keyword: keyword.value } : {}),
      ...(statusFilter.value ? { status: statusFilter.value } : {}),
      ...(levelFilter.value !== 0 ? { level: levelFilter.value as WarningLevel } : {}),
    };
    const result = await warningsApi.listAdmin(params);
    items.value = result.items;
    total.value = result.total;
  } catch (e) {
    if (e instanceof ApiError) errored.value = true;
    items.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function applyFilters(): void {
  page.value = 1;
  void load();
}

function resetFilters(): void {
  page.value = 1;
  keyword.value = "";
  statusFilter.value = "";
  levelFilter.value = 0;
  void load();
}

function openNew(): void {
  void router.push({ name: "admin-warning-new" });
}

function openDetail(row: WarningListItem): void {
  void router.push({
    name: "admin-warning-detail",
    params: { warning_id: row.warning_id },
  });
}

async function appendNotice(row: WarningListItem): Promise<void> {
  if (row.status !== "ONLINE") {
    ElMessage.warning("仅上线中的预警可追加说明");
    return;
  }
  try {
    const { value } = await ElMessageBox.prompt(
      "追加内容（≥5 字）",
      `追加说明 · ${row.title}`,
      {
        confirmButtonText: "提交追加",
        cancelButtonText: "取消",
        inputType: "textarea",
        inputValidator: (v: string) =>
          (v?.trim().length ?? 0) >= 5 || "追加内容至少 5 字",
      },
    );
    await warningsApi.append(row.warning_id, { appendix: String(value).trim() });
    ElMessage.success("追加说明已提交");
    await load();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

async function offlineNotice(row: WarningListItem): Promise<void> {
  if (row.status !== "ONLINE") {
    ElMessage.warning("仅上线中的预警可下线");
    return;
  }
  try {
    const { value } = await ElMessageBox.prompt(
      "下线原因（≥5 字）",
      `手动下线 · ${row.title}`,
      {
        confirmButtonText: "确认下线",
        cancelButtonText: "取消",
        confirmButtonClass: "el-button--danger",
        inputType: "textarea",
        inputValidator: (v: string) =>
          (v?.trim().length ?? 0) >= 5 || "下线原因至少 5 字",
      },
    );
    await warningsApi.offline(row.warning_id, { reason: String(value).trim() });
    ElMessage.success("已下线");
    await load();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

function prevPage(): void {
  if (page.value > 1) {
    page.value -= 1;
    void load();
  }
}

function nextPage(): void {
  if (page.value < totalPages.value) {
    page.value += 1;
    void load();
  }
}

onMounted(load);
</script>

<template>
  <div class="admin-warning-list">
    <AppPageHeader
      badge="UC-07"
      title="预警公告"
      :subtitle="`共 ${total} 条预警（含已下线）`"
    >
      <template #actions>
        <AppButton variant="primary" size="md" @click="openNew">
          <AppIcon name="plus" :size="14" />
          发布预警
        </AppButton>
      </template>
    </AppPageHeader>

    <AppCard padding="md">
      <div class="admin-warning-list__filters">
        <div class="admin-warning-list__filter-group">
          <span class="admin-warning-list__filter-label">状态</span>
          <button
            v-for="opt in STATUS_OPTIONS"
            :key="opt.label"
            type="button"
            class="admin-warning-list__chip"
            :class="{ 'admin-warning-list__chip--active': statusFilter === opt.value }"
            @click="statusFilter = opt.value; applyFilters()"
          >
            {{ opt.label }}
          </button>
        </div>
        <div class="admin-warning-list__filter-group">
          <span class="admin-warning-list__filter-label">级别</span>
          <button
            v-for="opt in LEVEL_OPTIONS"
            :key="opt.label"
            type="button"
            class="admin-warning-list__chip"
            :class="{ 'admin-warning-list__chip--active': levelFilter === opt.value }"
            @click="levelFilter = opt.value; applyFilters()"
          >
            {{ opt.label }}
          </button>
        </div>
        <div
          class="admin-warning-list__filter-group admin-warning-list__filter-group--search"
        >
          <input
            v-model="keyword"
            class="admin-warning-list__search"
            type="search"
            placeholder="搜索标题 / 内容关键词"
            @keyup.enter="applyFilters"
          >
          <AppButton variant="primary" size="sm" @click="applyFilters">
            <AppIcon name="search" :size="14" />
            搜索
          </AppButton>
          <AppButton variant="ghost" size="sm" @click="resetFilters">
            重置
          </AppButton>
        </div>
      </div>
    </AppCard>

    <AppErrorState
      v-if="errored"
      title="加载失败"
      hint="请稍后重试"
      retry-label="重新加载"
      @retry="load"
    />
    <AppCard v-else padding="none">
      <div v-if="loading" class="admin-warning-list__loading">
        <AppIcon name="loader" :size="22" class="admin-warning-list__spin" />
        加载中…
      </div>
      <div v-else-if="items.length === 0" class="admin-warning-list__empty">
        <AppEmpty
          title="暂无预警"
          hint="点击右上角「发布预警」开始发布"
          illustration="warning"
        />
      </div>
      <div v-else class="admin-warning-list__table-wrap">
        <table class="admin-warning-list__table">
          <thead>
            <tr>
              <th>标题</th>
              <th>等级</th>
              <th>推送范围</th>
              <th>状态</th>
              <th>发布人</th>
              <th>发布时间</th>
              <th class="admin-warning-list__th-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in items"
              :key="row.warning_id"
              class="admin-warning-list__row"
              @click="openDetail(row)"
            >
              <td class="admin-warning-list__title-cell">{{ row.title }}</td>
              <td>
                <AppStatusTag
                  :status="'info'"
                  :warn-level="warnLevelClass(row.warning_level)"
                  :text="`${WARNING_LEVEL_LABEL[row.warning_level]}级`"
                />
              </td>
              <td>{{ WARNING_SCOPE_LABEL[row.push_scope] }}</td>
              <td>
                <AppStatusTag
                  :status="row.status === 'ONLINE' ? 'success' : 'neutral'"
                  :text="WARNING_STATUS_LABEL[row.status] ?? row.status"
                />
              </td>
              <td>{{ row.publisher_name || "—" }}</td>
              <td>{{ formatDate(row.published_at) }}</td>
              <td class="admin-warning-list__actions-cell" @click.stop>
                <div class="admin-warning-list__actions">
                  <AppButton variant="ghost" size="sm" @click="openDetail(row)">
                    <AppIcon name="eye" :size="13" />
                    详情
                  </AppButton>
                  <AppButton
                    variant="ghost"
                    size="sm"
                    :disabled="row.status !== 'ONLINE'"
                    @click="appendNotice(row)"
                  >
                    <AppIcon name="edit" :size="13" />
                    追加
                  </AppButton>
                  <AppButton
                    variant="ghost"
                    size="sm"
                    :disabled="row.status !== 'ONLINE'"
                    @click="offlineNotice(row)"
                  >
                    <AppIcon name="x" :size="13" />
                    下线
                  </AppButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </AppCard>

    <div v-if="!errored && total > size" class="admin-warning-list__pager">
      <AppButton variant="ghost" size="sm" :disabled="page <= 1" @click="prevPage">
        上一页
      </AppButton>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <AppButton
        variant="ghost"
        size="sm"
        :disabled="page >= totalPages"
        @click="nextPage"
      >
        下一页
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.admin-warning-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-warning-list__filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.admin-warning-list__filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.admin-warning-list__filter-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  min-width: 36px;
}

.admin-warning-list__chip {
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

.admin-warning-list__chip:hover {
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.admin-warning-list__chip--active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
}

.admin-warning-list__search {
  flex: 1;
  min-width: 200px;
  padding: 8px var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--font-size-sm);
  font-family: inherit;
  transition: border-color var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out);
}

.admin-warning-list__search:focus {
  outline: none;
  border-color: var(--color-brand-500);
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.admin-warning-list__loading,
.admin-warning-list__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  gap: var(--space-2);
}

.admin-warning-list__spin {
  animation: admin-warning-spin 1s linear infinite;
}

@keyframes admin-warning-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.admin-warning-list__table-wrap {
  overflow-x: auto;
}

.admin-warning-list__table {
  width: 100%;
  border-collapse: collapse;
}

.admin-warning-list__table th,
.admin-warning-list__table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  white-space: nowrap;
  vertical-align: middle;
}

.admin-warning-list__table thead th {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--color-bg-soft);
}

.admin-warning-list__row {
  cursor: pointer;
  transition: background var(--duration-fast) var(--easing-out);
}

.admin-warning-list__row:hover {
  background: var(--color-bg-soft);
}

.admin-warning-list__title-cell {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
  white-space: normal;
  min-width: 220px;
}

.admin-warning-list__th-actions {
  text-align: right !important;
}

.admin-warning-list__actions-cell {
  text-align: right;
}

.admin-warning-list__actions {
  display: inline-flex;
  gap: 4px;
}

.admin-warning-list__pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
