<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { useAuthStore } from "@/stores/auth";
import { reportsApi } from "@/api/reports";
import type { FraudType } from "@/types/report";
import {
  knowledgeApi,
  KNOWLEDGE_STATUS_LABEL,
  KNOWLEDGE_STATUS_TONE,
  type KnowledgeAdminListParams,
  type KnowledgeListItem,
  type KnowledgeStatus,
} from "@/api/knowledge";
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
const auth = useAuthStore();

const loading = ref(false);
const errored = ref(false);
const items = ref<KnowledgeListItem[]>([]);
const total = ref(0);

const fraudTypes = ref<FraudType[]>([]);

const page = ref(1);
const size = ref(15);
const keyword = ref("");
const statusFilter = ref<KnowledgeStatus | "ALL">("ALL");
const fraudTypeId = ref<number | null>(null);

const STATUS_OPTIONS: ReadonlyArray<{ value: KnowledgeStatus | "ALL"; label: string }> = [
  { value: "ALL", label: "全部" },
  { value: "DRAFT", label: "草稿" },
  { value: "PENDING", label: "待审核" },
  { value: "PUBLISHED", label: "已发布" },
  { value: "OFFLINE", label: "已下线" },
];

const totalPages = computed<number>(() =>
  Math.max(1, Math.ceil(total.value / size.value)),
);

const canReview = computed<boolean>(() => auth.hasPermission("kb:review"));
const canOffline = computed<boolean>(() => auth.hasPermission("kb:offline"));

function isAuthor(row: KnowledgeListItem): boolean {
  return auth.me?.user_id != null && row.author_id === auth.me.user_id;
}

function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 16).replace("T", " ");
}

async function loadFraudTypes(): Promise<void> {
  try {
    fraudTypes.value = await reportsApi.listFraudTypes();
  } catch {
    fraudTypes.value = [];
  }
}

async function load(): Promise<void> {
  loading.value = true;
  errored.value = false;
  try {
    const params: KnowledgeAdminListParams = {
      page: page.value,
      size: size.value,
      ...(keyword.value ? { keyword: keyword.value } : {}),
      ...(statusFilter.value !== "ALL" ? { status: [statusFilter.value] } : {}),
      ...(fraudTypeId.value != null ? { fraud_type_id: fraudTypeId.value } : {}),
    };
    const result = await knowledgeApi.listAdmin(params);
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
  statusFilter.value = "ALL";
  fraudTypeId.value = null;
  void load();
}

function openNew(): void {
  void router.push({ name: "admin-kb-new" });
}

function openDetail(row: KnowledgeListItem): void {
  void router.push({
    name: "admin-kb-detail",
    params: { entry_id: row.entry_id },
  });
}

function openEdit(row: KnowledgeListItem): void {
  void router.push({
    name: "admin-kb-edit",
    params: { entry_id: row.entry_id },
  });
}

async function submitForReview(row: KnowledgeListItem): Promise<void> {
  if (row.status !== "DRAFT") {
    ElMessage.warning("仅草稿状态可提交审核");
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确定将《${row.title}》提交校级审核？`,
      "提交审核",
      {
        confirmButtonText: "提交",
        cancelButtonText: "取消",
      },
    );
    await knowledgeApi.submit(row.entry_id);
    ElMessage.success("已提交审核");
    await load();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

async function offlineEntry(row: KnowledgeListItem): Promise<void> {
  if (row.status !== "PUBLISHED") {
    ElMessage.warning("仅已发布的条目可下线");
    return;
  }
  try {
    const { value } = await ElMessageBox.prompt(
      "下线原因（≥5 字）",
      `下线 · ${row.title}`,
      {
        confirmButtonText: "确认下线",
        cancelButtonText: "取消",
        confirmButtonClass: "el-button--danger",
        inputType: "textarea",
        inputValidator: (v: string) =>
          (v?.trim().length ?? 0) >= 5 || "下线原因至少 5 字",
      },
    );
    await knowledgeApi.offline(row.entry_id, { reason: String(value).trim() });
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

onMounted(async () => {
  await Promise.all([loadFraudTypes(), load()]);
});
</script>

<template>
  <div class="admin-kb-list">
    <AppPageHeader
      badge="UC-04"
      title="知识库管理"
      :subtitle="`共 ${total} 条（含草稿、待审核、已发布、已下线）`"
    >
      <template #actions>
        <AppButton variant="primary" size="md" @click="openNew">
          <AppIcon name="plus" :size="14" />
          新建条目
        </AppButton>
      </template>
    </AppPageHeader>

    <AppCard padding="md">
      <div class="admin-kb-list__filters">
        <div class="admin-kb-list__filter-group">
          <span class="admin-kb-list__filter-label">状态</span>
          <button
            v-for="opt in STATUS_OPTIONS"
            :key="opt.value"
            type="button"
            class="admin-kb-list__chip"
            :class="{ 'admin-kb-list__chip--active': statusFilter === opt.value }"
            @click="statusFilter = opt.value; applyFilters()"
          >
            {{ opt.label }}
          </button>
        </div>
        <div class="admin-kb-list__filter-group">
          <span class="admin-kb-list__filter-label">类型</span>
          <button
            type="button"
            class="admin-kb-list__chip"
            :class="{ 'admin-kb-list__chip--active': fraudTypeId === null }"
            @click="fraudTypeId = null; applyFilters()"
          >
            全部类型
          </button>
          <button
            v-for="ft in fraudTypes"
            :key="ft.type_id"
            type="button"
            class="admin-kb-list__chip"
            :class="{ 'admin-kb-list__chip--active': fraudTypeId === ft.type_id }"
            @click="fraudTypeId = ft.type_id; applyFilters()"
          >
            {{ ft.type_name }}
          </button>
        </div>
        <div class="admin-kb-list__filter-group admin-kb-list__filter-group--search">
          <input
            v-model="keyword"
            class="admin-kb-list__search"
            type="search"
            placeholder="搜索标题 / 摘要关键词"
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
      <div v-if="loading" class="admin-kb-list__loading">
        <AppIcon name="loader" :size="22" class="admin-kb-list__spin" />
        加载中…
      </div>
      <div v-else-if="items.length === 0" class="admin-kb-list__empty">
        <AppEmpty
          title="暂无知识条目"
          hint="点击右上角「新建条目」开始撰写"
          illustration="search"
        />
      </div>
      <div v-else class="admin-kb-list__table-wrap">
        <table class="admin-kb-list__table">
          <thead>
            <tr>
              <th>标题</th>
              <th>诈骗类型</th>
              <th>状态</th>
              <th>版本</th>
              <th>作者</th>
              <th>更新时间</th>
              <th class="admin-kb-list__th-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in items"
              :key="row.entry_id"
              class="admin-kb-list__row"
              @click="openDetail(row)"
            >
              <td class="admin-kb-list__title-cell">{{ row.title }}</td>
              <td>{{ row.fraud_type_name || "—" }}</td>
              <td>
                <AppStatusTag
                  :status="KNOWLEDGE_STATUS_TONE[row.status] ?? 'neutral'"
                  :text="KNOWLEDGE_STATUS_LABEL[row.status] ?? row.status"
                />
              </td>
              <td><code>v{{ row.version }}</code></td>
              <td>{{ row.author_name || "—" }}</td>
              <td>{{ formatDate(row.updated_at) }}</td>
              <td class="admin-kb-list__actions-cell" @click.stop>
                <div class="admin-kb-list__actions">
                  <AppButton variant="ghost" size="sm" @click="openDetail(row)">
                    <AppIcon name="eye" :size="13" />
                    详情
                  </AppButton>
                  <AppButton
                    v-if="row.status === 'DRAFT' && isAuthor(row)"
                    variant="ghost"
                    size="sm"
                    @click="openEdit(row)"
                  >
                    <AppIcon name="edit" :size="13" />
                    编辑
                  </AppButton>
                  <AppButton
                    v-if="row.status === 'DRAFT' && isAuthor(row)"
                    variant="primary"
                    size="sm"
                    @click="submitForReview(row)"
                  >
                    <AppIcon name="send" :size="13" />
                    提交审核
                  </AppButton>
                  <AppButton
                    v-if="row.status === 'PENDING' && canReview"
                    variant="primary"
                    size="sm"
                    @click="openDetail(row)"
                  >
                    <AppIcon name="circle-check" :size="13" />
                    审核
                  </AppButton>
                  <AppButton
                    v-if="row.status === 'PUBLISHED' && canOffline"
                    variant="ghost"
                    size="sm"
                    @click="offlineEntry(row)"
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

    <div v-if="!errored && total > size" class="admin-kb-list__pager">
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
.admin-kb-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-kb-list__filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.admin-kb-list__filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.admin-kb-list__filter-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  min-width: 36px;
}

.admin-kb-list__chip {
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

.admin-kb-list__chip:hover {
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.admin-kb-list__chip--active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
}

.admin-kb-list__search {
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

.admin-kb-list__search:focus {
  outline: none;
  border-color: var(--color-brand-500);
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.admin-kb-list__loading,
.admin-kb-list__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  gap: var(--space-2);
}

.admin-kb-list__spin {
  animation: admin-kb-spin 1s linear infinite;
}

@keyframes admin-kb-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.admin-kb-list__table-wrap {
  overflow-x: auto;
}

.admin-kb-list__table {
  width: 100%;
  border-collapse: collapse;
}

.admin-kb-list__table th,
.admin-kb-list__table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  white-space: nowrap;
  vertical-align: middle;
}

.admin-kb-list__table thead th {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--color-bg-soft);
}

.admin-kb-list__row {
  cursor: pointer;
  transition: background var(--duration-fast) var(--easing-out);
}

.admin-kb-list__row:hover {
  background: var(--color-bg-soft);
}

.admin-kb-list__title-cell {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
  white-space: normal;
  min-width: 220px;
}

.admin-kb-list__th-actions {
  text-align: right !important;
}

.admin-kb-list__actions-cell {
  text-align: right;
}

.admin-kb-list__actions {
  display: inline-flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.admin-kb-list__pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
