<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { reportsApi } from "@/api/reports";
import type { FraudType } from "@/types/report";
import {
  knowledgeApi,
  type KnowledgeListItem,
  type KnowledgeListParams,
  type KnowledgeListSort,
} from "@/api/knowledge";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppEmpty,
  AppErrorState,
  AppIcon,
  AppPageHeader,
} from "@/components";

const router = useRouter();

const loading = ref(false);
const errored = ref(false);
const items = ref<KnowledgeListItem[]>([]);
const total = ref(0);

const fraudTypes = ref<FraudType[]>([]);
const fraudTypeId = ref<number | null>(null);
const keyword = ref("");
const sort = ref<KnowledgeListSort>("published_at_desc");
const page = ref(1);
const size = ref(12);

const SORT_OPTIONS: ReadonlyArray<{ value: KnowledgeListSort; label: string }> = [
  { value: "published_at_desc", label: "最新发布" },
  { value: "hot", label: "热门" },
];

const totalPages = computed<number>(() =>
  Math.max(1, Math.ceil(total.value / size.value)),
);

function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 10);
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
    const params: KnowledgeListParams = {
      page: page.value,
      size: size.value,
      sort: sort.value,
      ...(keyword.value ? { keyword: keyword.value } : {}),
      ...(fraudTypeId.value != null ? { fraud_type_id: fraudTypeId.value } : {}),
    };
    const result = await knowledgeApi.listPublic(params);
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
  fraudTypeId.value = null;
  sort.value = "published_at_desc";
  void load();
}

function openDetail(item: KnowledgeListItem): void {
  void router.push({
    name: "kb-detail",
    params: { entry_id: item.entry_id },
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

onMounted(async () => {
  await Promise.all([loadFraudTypes(), load()]);
});
</script>

<template>
  <div class="kb-list">
    <AppPageHeader
      title="反诈知识库"
      :subtitle="`已发布反诈案例与防范建议，共 ${total} 条`"
    />

    <AppCard padding="md">
      <div class="kb-list__filters">
        <div class="kb-list__filter-group">
          <span class="kb-list__filter-label">类型</span>
          <button
            type="button"
            class="kb-list__chip"
            :class="{ 'kb-list__chip--active': fraudTypeId === null }"
            @click="fraudTypeId = null; applyFilters()"
          >
            全部类型
          </button>
          <button
            v-for="ft in fraudTypes"
            :key="ft.type_id"
            type="button"
            class="kb-list__chip"
            :class="{ 'kb-list__chip--active': fraudTypeId === ft.type_id }"
            @click="fraudTypeId = ft.type_id; applyFilters()"
          >
            {{ ft.type_name }}
          </button>
        </div>
        <div class="kb-list__filter-group">
          <span class="kb-list__filter-label">排序</span>
          <button
            v-for="opt in SORT_OPTIONS"
            :key="opt.value"
            type="button"
            class="kb-list__chip"
            :class="{ 'kb-list__chip--active': sort === opt.value }"
            @click="sort = opt.value; applyFilters()"
          >
            {{ opt.label }}
          </button>
        </div>
        <div class="kb-list__filter-group kb-list__filter-group--search">
          <input
            v-model="keyword"
            class="kb-list__search"
            type="search"
            placeholder="搜索标题 / 摘要"
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
      title="知识库加载失败"
      hint="请检查网络后重试"
      retry-label="重新加载"
      @retry="load"
    />
    <template v-else>
      <div v-if="loading" class="kb-list__loading">
        <AppIcon name="loader" :size="22" class="kb-list__spin" />
        加载中…
      </div>
      <AppCard v-else-if="items.length === 0" padding="md">
        <AppEmpty
          title="暂无知识条目"
          hint="试试更换筛选条件"
          illustration="search"
        />
      </AppCard>
      <div v-else class="kb-list__grid">
        <article
          v-for="item in items"
          :key="item.entry_id"
          class="kb-list__card"
          @click="openDetail(item)"
        >
          <span class="kb-list__card-corner" aria-hidden="true" />
          <div class="kb-list__card-tag">
            <AppIcon name="tag" :size="12" />
            {{ item.fraud_type_name || "通用" }}
          </div>
          <h3 class="kb-list__card-title">{{ item.title }}</h3>
          <p class="kb-list__card-summary">{{ item.desensitized_summary }}</p>
          <div class="kb-list__card-meta">
            <span class="kb-list__card-meta-cell">
              <AppIcon name="user" :size="13" />
              {{ item.author_name || "—" }}
            </span>
            <span class="kb-list__card-meta-cell">
              <AppIcon name="clock" :size="13" />
              {{ formatDate(item.published_at) }}
            </span>
            <span class="kb-list__card-meta-cell">
              <AppIcon name="info" :size="13" />
              v{{ item.version }}
            </span>
          </div>
        </article>
      </div>
    </template>

    <div v-if="!errored && total > size" class="kb-list__pager">
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
.kb-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.kb-list__filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.kb-list__filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.kb-list__filter-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  min-width: 36px;
}

.kb-list__chip {
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

.kb-list__chip:hover {
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.kb-list__chip--active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
  box-shadow: var(--shadow-glow-brand);
}

.kb-list__search {
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

.kb-list__search:focus {
  outline: none;
  border-color: var(--color-brand-500);
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.kb-list__loading {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.kb-list__spin {
  animation: kb-list-spin 1s linear infinite;
}

@keyframes kb-list-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.kb-list__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.kb-list__card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  cursor: pointer;
  transition:
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
  overflow: hidden;
}

.kb-list__card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-mid);
  border-color: var(--color-brand-300);
}

.kb-list__card-corner {
  position: absolute;
  top: 0;
  left: 0;
  width: 16px;
  height: 16px;
  border-top: 2px solid var(--color-gold-400);
  border-left: 2px solid var(--color-gold-400);
  border-top-left-radius: var(--radius-lg);
  pointer-events: none;
}

.kb-list__card-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  font-size: 10.5px;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
  width: fit-content;
}

.kb-list__card-title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-list__card-summary {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-list__card-meta {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--color-border);
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.kb-list__card-meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.kb-list__pager {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
