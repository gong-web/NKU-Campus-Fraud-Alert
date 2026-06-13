<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  warningsApi,
  WARNING_LEVEL_LABEL,
  WARNING_SCOPE_LABEL,
  WARNING_STATUS_LABEL,
  type WarningLevel,
  type WarningListItem,
  type WarningListParams,
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
const size = ref(10);
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

function warnLevelClass(
  level: WarningLevel,
): "info" | "warning" | "urgent" {
  if (level === 3) return "urgent";
  if (level === 2) return "warning";
  return "info";
}

function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  const dt = new Date(d);
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(dt);
}

async function load(): Promise<void> {
  loading.value = true;
  errored.value = false;
  try {
    const params: WarningListParams = {
      page: page.value,
      size: size.value,
      ...(keyword.value ? { keyword: keyword.value } : {}),
      ...(statusFilter.value ? { status: statusFilter.value } : {}),
      ...(levelFilter.value !== 0 ? { level: levelFilter.value as WarningLevel } : {}),
    };
    const result = await warningsApi.listMine(params);
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

function openDetail(item: WarningListItem): void {
  void router.push({
    name: "warning-detail",
    params: { warning_id: item.warning_id },
  });
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
  <div class="warning-list">
    <AppPageHeader
      title="安全预警"
      :subtitle="`本人可见预警，共 ${total} 条`"
    />

    <!-- 筛选条 -->
    <AppCard padding="md">
      <div class="warning-list__filters">
        <div class="warning-list__filter-group">
          <span class="warning-list__filter-label">状态</span>
          <button
            v-for="opt in STATUS_OPTIONS"
            :key="opt.label"
            type="button"
            class="warning-list__chip"
            :class="{ 'warning-list__chip--active': statusFilter === opt.value }"
            @click="statusFilter = opt.value; applyFilters()"
          >
            {{ opt.label }}
          </button>
        </div>
        <div class="warning-list__filter-group">
          <span class="warning-list__filter-label">级别</span>
          <button
            v-for="opt in LEVEL_OPTIONS"
            :key="opt.label"
            type="button"
            class="warning-list__chip"
            :class="{ 'warning-list__chip--active': levelFilter === opt.value }"
            @click="levelFilter = opt.value; applyFilters()"
          >
            {{ opt.label }}
          </button>
        </div>
        <div class="warning-list__filter-group warning-list__filter-group--search">
          <input
            v-model="keyword"
            class="warning-list__search"
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

    <!-- 列表 -->
    <AppErrorState
      v-if="errored"
      title="预警加载失败"
      hint="请检查网络后重试"
      retry-label="重新加载"
      @retry="load"
    />
    <AppCard v-else padding="none">
      <div v-if="loading" class="warning-list__loading">
        <AppIcon name="loader" :size="22" class="warning-list__spin" />
        加载中…
      </div>
      <div v-else-if="items.length === 0" class="warning-list__empty">
        <AppEmpty
          title="暂无预警"
          hint="当前没有面向你的安全预警"
          illustration="warning"
        />
      </div>
      <ul v-else class="warning-list__items">
        <li
          v-for="w in items"
          :key="w.warning_id"
          class="warning-list__item"
          :class="[
            `warning-list__item--${warnLevelClass(w.warning_level)}`,
          ]"
          @click="openDetail(w)"
        >
          <span class="warning-list__item-bar" aria-hidden="true" />
          <div class="warning-list__item-body">
            <div class="warning-list__item-head">
              <AppStatusTag
                :status="'info'"
                :warn-level="warnLevelClass(w.warning_level)"
                :text="`${WARNING_LEVEL_LABEL[w.warning_level]}级`"
              />
              <span
                v-if="w.status === 'OFFLINE'"
                class="warning-list__offline"
              >已下线</span>
            </div>
            <h3 class="warning-list__item-title">{{ w.title }}</h3>
            <div class="warning-list__item-meta">
              <span class="warning-list__meta-cell">
                <AppIcon name="users" :size="13" />
                {{ WARNING_SCOPE_LABEL[w.push_scope] ?? w.push_scope }}
              </span>
              <span class="warning-list__meta-cell">
                <AppIcon name="user" :size="13" />
                {{ w.publisher_name || "—" }}
              </span>
              <span class="warning-list__meta-cell">
                <AppIcon name="clock" :size="13" />
                {{ formatDate(w.published_at) }}
              </span>
              <span class="warning-list__meta-cell">
                <AppIcon name="info" :size="13" />
                状态 · {{ WARNING_STATUS_LABEL[w.status] ?? w.status }}
              </span>
            </div>
          </div>
          <AppIcon name="chevron-right" :size="18" class="warning-list__item-arrow" />
        </li>
      </ul>
    </AppCard>

    <!-- 分页 -->
    <div v-if="!errored && total > size" class="warning-list__pager">
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
.warning-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.warning-list__filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.warning-list__filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.warning-list__filter-group--search {
  gap: var(--space-2);
}

.warning-list__filter-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  min-width: 36px;
}

.warning-list__chip {
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

.warning-list__chip:hover {
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.warning-list__chip--active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
  box-shadow: var(--shadow-glow-brand);
}

.warning-list__search {
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

.warning-list__search:focus {
  outline: none;
  border-color: var(--color-brand-500);
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.warning-list__loading,
.warning-list__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: 320px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.warning-list__spin {
  animation: warning-list-spin 1s linear infinite;
}

@keyframes warning-list-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.warning-list__items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.warning-list__item {
  position: relative;
  display: grid;
  grid-template-columns: 4px 1fr 24px;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background var(--duration-base) var(--easing-out);
  align-items: center;
}

.warning-list__item:last-child {
  border-bottom: none;
}

.warning-list__item:hover {
  background: var(--color-bg-soft);
}

.warning-list__item-bar {
  width: 4px;
  align-self: stretch;
  border-radius: 2px;
}

.warning-list__item--info .warning-list__item-bar {
  background: var(--color-warn-info, var(--color-info));
}

.warning-list__item--warning .warning-list__item-bar {
  background: var(--color-warn-warning, var(--color-warning));
}

.warning-list__item--urgent .warning-list__item-bar {
  background: var(--color-warn-urgent, var(--color-danger));
}

.warning-list__item-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.warning-list__item-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.warning-list__item-title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  line-height: 1.4;
  letter-spacing: -0.01em;
}

.warning-list__item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.warning-list__meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.warning-list__offline {
  font-size: 10.5px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-neutral-100);
  color: var(--color-neutral-600);
  letter-spacing: 0.04em;
}

.warning-list__item-arrow {
  color: var(--color-text-tertiary);
  transition: transform var(--duration-base) var(--easing-out);
}

.warning-list__item:hover .warning-list__item-arrow {
  transform: translateX(2px);
  color: var(--color-brand-600);
}

.warning-list__pager {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
