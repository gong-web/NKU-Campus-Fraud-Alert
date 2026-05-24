<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  knowledgeApi,
  KNOWLEDGE_SOURCE_LABEL,
  type KnowledgeDetail,
  type KnowledgeListItem,
} from "@/api/knowledge";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppErrorState,
  AppIcon,
  AppPageHeader,
  AppSkeleton,
} from "@/components";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const errored = ref(false);
const errorMsg = ref("");
const entry = ref<KnowledgeDetail | null>(null);

function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 10);
}

async function load(): Promise<void> {
  const entryId = String(route.params.entry_id ?? "");
  if (!entryId) {
    errored.value = true;
    errorMsg.value = "缺少条目编号";
    return;
  }
  loading.value = true;
  errored.value = false;
  errorMsg.value = "";
  try {
    entry.value = await knowledgeApi.getPublic(entryId);
  } catch (e) {
    errored.value = true;
    errorMsg.value = e instanceof ApiError ? e.message : "加载失败";
    entry.value = null;
  } finally {
    loading.value = false;
  }
}

function goRelated(item: KnowledgeListItem): void {
  void router.push({
    name: "kb-detail",
    params: { entry_id: item.entry_id },
  });
}

function goBack(): void {
  if (route.query.from === "quiz-wrong") {
    void router.push({ name: "quiz-wrong" });
    return;
  }
  if (route.query.from === "quiz-answer") {
    const attemptId = String(route.query.attempt_id ?? "");
    if (attemptId) {
      void router.push({ name: "quiz-answer", params: { attempt_id: attemptId } });
      return;
    }
  }
  void router.push({ name: "kb-list" });
}

onMounted(load);
</script>

<template>
  <div class="kb-detail">
    <AppPageHeader badge="UC-08" title="知识详情">
      <template #actions>
        <AppButton variant="ghost" size="sm" @click="goBack">
          <AppIcon name="arrow-left" :size="14" />
          {{ route.query.from === "quiz-wrong" ? "返回错题本" : route.query.from === "quiz-answer" ? "返回测验" : "返回知识库" }}
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
        <AppSkeleton :rows="8" />
      </AppCard>
      <template v-else-if="entry">
        <AppCard padding="lg" :corner="true">
          <div class="kb-detail__hero-tags">
            <span class="kb-detail__tag">
              <AppIcon name="tag" :size="12" />
              {{ entry.fraud_type_name || "通用" }}
            </span>
            <span class="kb-detail__tag kb-detail__tag--source">
              <AppIcon name="info" :size="12" />
              {{ KNOWLEDGE_SOURCE_LABEL[entry.source_type] ?? entry.source_type }}
            </span>
            <span class="kb-detail__tag kb-detail__tag--ver">
              v{{ entry.version }}
            </span>
          </div>
          <h2 class="kb-detail__title">{{ entry.title }}</h2>
          <div class="kb-detail__meta">
            <span class="kb-detail__meta-cell">
              <AppIcon name="user" :size="13" />
              {{ entry.author_name || "—" }}
            </span>
            <span class="kb-detail__meta-cell">
              <AppIcon name="clock" :size="13" />
              发布于 {{ formatDate(entry.published_at) }}
            </span>
            <span v-if="entry.peak_periods" class="kb-detail__meta-cell">
              <AppIcon name="calendar" :size="13" />
              高发期 · {{ entry.peak_periods }}
            </span>
          </div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>案情概要</h3>
              <small>已脱敏处理，仅保留可分享要素</small>
            </div>
          </template>
          <div class="kb-detail__content">{{ entry.desensitized_summary }}</div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>识别要点</h3>
              <small>遇到下列特征立即提高警惕</small>
            </div>
          </template>
          <div class="kb-detail__content kb-detail__content--accent">
            {{ entry.identification_points }}
          </div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>防范建议</h3>
              <small>按以下建议处置可显著降低风险</small>
            </div>
          </template>
          <div class="kb-detail__content">{{ entry.prevention_advice }}</div>
        </AppCard>

        <AppCard v-if="entry.source_reference" padding="md">
          <div class="kb-detail__source">
            <AppIcon name="file-text" :size="14" />
            <span>来源参考</span>
            <span class="kb-detail__source-text">{{ entry.source_reference }}</span>
          </div>
        </AppCard>

        <section v-if="entry.related.length > 0" class="kb-detail__related-section">
          <h3 class="kb-detail__related-title">
            <AppIcon name="sparkles" :size="14" />
            相关推荐
          </h3>
          <div class="kb-detail__related-grid">
            <article
              v-for="r in entry.related"
              :key="r.entry_id"
              class="kb-detail__related-card"
              @click="goRelated(r)"
            >
              <h4>{{ r.title }}</h4>
              <p>{{ r.desensitized_summary }}</p>
              <span class="kb-detail__related-meta">
                <AppIcon name="clock" :size="12" />
                {{ formatDate(r.published_at) }}
              </span>
            </article>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
.kb-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.kb-detail__hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.kb-detail__tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
}

.kb-detail__tag--source {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
}

.kb-detail__tag--ver {
  background: var(--color-neutral-100);
  color: var(--color-neutral-600);
  font-family: var(--font-family-mono);
}

.kb-detail__title {
  margin: 0 0 var(--space-3);
  font-family: var(--font-family-serif);
  font-size: clamp(22px, 2.6vw, 32px);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.kb-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-4);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.kb-detail__meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.kb-detail__content {
  font-size: var(--font-size-sm);
  line-height: 1.85;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}

.kb-detail__content--accent {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(239 108 0 / 4%);
  border-left: 3px solid var(--color-warning);
}

.kb-detail__source {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.kb-detail__source-text {
  font-family: var(--font-family-mono);
  background: var(--color-bg-soft);
  border: 1px solid var(--color-border);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  color: var(--color-text);
  word-break: break-all;
}

.kb-detail__related-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.kb-detail__related-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.kb-detail__related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-3);
}

.kb-detail__related-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    border-color var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out);
}

.kb-detail__related-card:hover {
  border-color: var(--color-brand-300);
  box-shadow: var(--shadow-low);
}

.kb-detail__related-card h4 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-detail__related-card p {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-detail__related-meta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-top: auto;
}
</style>
