<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { quizApi, QUIZ_STATUS_LABEL } from "@/api/quiz";
import type { QuizListItem, QuizStatus } from "@/types/quiz";
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
const items = ref<QuizListItem[]>([]);
const total = ref(0);

const page = ref(1);
const size = ref(10);
const statusFilter = ref<QuizStatus | "">("");
const keyword = ref("");

const STATUS_OPTIONS: ReadonlyArray<{ value: QuizStatus | ""; label: string }> = [
  { value: "", label: "全部" },
  { value: "ACTIVE", label: "进行中" },
  { value: "FINISHED", label: "已结束" },
  { value: "CANCELLED", label: "已撤回" },
];

const totalPages = computed<number>(() =>
  Math.max(1, Math.ceil(total.value / size.value)),
);

function quizStatusTone(
  s: QuizStatus,
): "success" | "warning" | "neutral" {
  if (s === "ACTIVE") return "success";
  if (s === "FINISHED") return "warning";
  return "neutral";
}

function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 16).replace("T", " ");
}

function publishLevelLabel(level: 1 | 2 | number | null | undefined): string {
  return level === 1 ? "学院" : "学校";
}

async function load(): Promise<void> {
  loading.value = true;
  errored.value = false;
  try {
    const r = await quizApi.listAdminQuizzes({
      page: page.value,
      size: size.value,
      ...(statusFilter.value ? { status: statusFilter.value } : {}),
      ...(keyword.value ? { keyword: keyword.value } : {}),
    });
    items.value = r.items;
    total.value = r.total;
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
  void load();
}

function openReport(row: QuizListItem): void {
  void router.push({
    name: "admin-quiz-report",
    params: { quiz_id: row.quiz_id },
  });
}

function createNew(): void {
  void router.push({ name: "admin-quiz-new" });
}

function openBank(): void {
  void router.push({ name: "admin-quiz-bank" });
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
  <div class="admin-quiz-list">
    <AppPageHeader
      title="安全测验"
      :subtitle="`共 ${total} 场测验（含进行中、已结束、已撤回）`"
    >
      <template #actions>
        <AppButton variant="secondary" size="md" @click="openBank">
          <AppIcon name="book-open" :size="14" />
          题库管理
        </AppButton>
        <AppButton variant="primary" size="md" @click="createNew">
          <AppIcon name="plus" :size="14" />
          发起测验
        </AppButton>
      </template>
    </AppPageHeader>

    <AppCard padding="md">
      <div class="admin-quiz-list__filters">
        <div class="admin-quiz-list__filter-group">
          <span class="admin-quiz-list__filter-label">状态</span>
          <button
            v-for="opt in STATUS_OPTIONS"
            :key="opt.label"
            type="button"
            class="admin-quiz-list__chip"
            :class="{
              'admin-quiz-list__chip--active': statusFilter === opt.value,
            }"
            @click="
              statusFilter = opt.value;
              applyFilters();
            "
          >
            {{ opt.label }}
          </button>
        </div>
        <div
          class="admin-quiz-list__filter-group admin-quiz-list__filter-group--search"
        >
          <input
            v-model="keyword"
            class="admin-quiz-list__search"
            type="search"
            placeholder="搜索测验标题"
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
      <div v-if="loading" class="admin-quiz-list__loading">
        <AppIcon name="loader" :size="22" class="admin-quiz-list__spin" />
        加载中…
      </div>
      <div v-else-if="items.length === 0" class="admin-quiz-list__empty">
        <AppEmpty
          title="暂无测验"
          hint="点击右上角发起测验，创建第一场指定测验"
          illustration="default"
        />
      </div>
      <div v-else class="admin-quiz-list__table-wrap">
        <table class="admin-quiz-list__table">
          <thead>
            <tr>
              <th>标题</th>
              <th class="admin-quiz-list__th-num">发布级别</th>
              <th class="admin-quiz-list__th-num">题数</th>
              <th class="admin-quiz-list__th-num">及格分</th>
              <th>截止</th>
              <th>状态</th>
              <th class="admin-quiz-list__th-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in items"
              :key="row.quiz_id"
              class="admin-quiz-list__row"
              @click="openReport(row)"
            >
              <td class="admin-quiz-list__title-cell">{{ row.title }}</td>
              <td class="admin-quiz-list__num-cell">
                {{ publishLevelLabel(row.publish_level) }}
              </td>
              <td class="admin-quiz-list__num-cell">
                {{ row.question_count }}
              </td>
              <td class="admin-quiz-list__num-cell">{{ row.pass_score }}</td>
              <td>{{ formatDate(row.deadline_at) }}</td>
              <td>
                <AppStatusTag
                  :status="quizStatusTone(row.status)"
                  :text="QUIZ_STATUS_LABEL[row.status] || row.status"
                />
              </td>
              <td class="admin-quiz-list__actions-cell" @click.stop>
                <AppButton
                  variant="ghost"
                  size="sm"
                  @click="openReport(row)"
                >
                  <AppIcon name="activity" :size="13" />
                  完成率报告
                </AppButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </AppCard>

    <div v-if="!errored && total > size" class="admin-quiz-list__pager">
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
.admin-quiz-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-quiz-list__filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.admin-quiz-list__filter-group {
  display: flex;
  align-items: left;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.admin-quiz-list__filter-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  min-width: 36px;
}

.admin-quiz-list__chip {
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

.admin-quiz-list__chip:hover {
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.admin-quiz-list__chip--active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
  box-shadow: var(--shadow-glow-brand);
}

.admin-quiz-list__search {
  flex: 1;
  min-width: 200px;
  padding: 8px var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--font-size-sm);
  font-family: inherit;
  transition:
    border-color var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out);
}

.admin-quiz-list__search:focus {
  outline: none;
  border-color: var(--color-brand-500);
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.admin-quiz-list__loading,
.admin-quiz-list__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  gap: var(--space-2);
}

.admin-quiz-list__spin {
  animation: admin-quiz-spin 1s linear infinite;
}

@keyframes admin-quiz-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.admin-quiz-list__table-wrap {
  overflow-x: auto;
}

.admin-quiz-list__table {
  width: 100%;
  border-collapse: collapse;
}

.admin-quiz-list__table th,
.admin-quiz-list__table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  white-space: nowrap;
  vertical-align: middle;
}

.admin-quiz-list__table thead th {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--color-bg-soft);
}

.admin-quiz-list__th-num {
  text-align: left !important;
}

.admin-quiz-list__th-actions {
  text-align: left !important;
}

.admin-quiz-list__row {
  cursor: pointer;
  transition: background var(--duration-fast) var(--easing-out);
}

.admin-quiz-list__row:hover {
  background: var(--color-bg-soft);
}

.admin-quiz-list__title-cell {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
  white-space: normal;
  min-width: 240px;
}

.admin-quiz-list__num-cell {
  text-align: left;
  font-family: var(--font-family-mono);
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
}

.admin-quiz-list__actions-cell {
  text-align: left;
}

.admin-quiz-list__pager {
  display: flex;
  justify-content: flex-end;
  align-items: left;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
