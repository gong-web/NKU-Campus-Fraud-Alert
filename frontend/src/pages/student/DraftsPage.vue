<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import type { DraftOut } from "@/api/reports";
import { reportsApi } from "@/api/reports";
import { AppButton, AppCard, AppIcon, AppPageHeader } from "@/components";

const router = useRouter();
const loading = ref(true);
const drafts = ref<DraftOut[]>([]);
const deletingId = ref<string | null>(null);

async function load() {
  loading.value = true;
  try {
    drafts.value = await reportsApi.listDrafts();
  } finally {
    loading.value = false;
  }
}

async function deleteDraft(id: string) {
  if (!confirm("确认删除该草稿？关联的证据图片也将一并删除。")) return;
  deletingId.value = id;
  try {
    await reportsApi.deleteDraft(id);
    drafts.value = drafts.value.filter((d) => d.draft_id !== id);
  } finally {
    deletingId.value = null;
  }
}

function formatDate(s: string) {
  return new Date(s).toLocaleDateString("zh-CN");
}

function daysLeft(expires: string) {
  const diff = new Date(expires).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / 86400000));
}

onMounted(load);
</script>

<template>
  <div class="drafts-page">
    <AppPageHeader
      badge="草稿箱"
      title="上报草稿"
      subtitle="草稿保存 30 天后自动清理"
    />

    <div
      v-if="loading"
      class="drafts-page__loading"
    >
      <AppIcon
        name="loader"
        :size="24"
        class="spin"
      />
      加载中…
    </div>

    <template v-else>
      <div
        v-if="drafts.length === 0"
        class="drafts-page__empty"
      >
        <AppCard padding="lg">
          <div class="drafts-page__empty-inner">
            <AppIcon
              name="file"
              :size="48"
            />
            <p>暂无草稿</p>
            <AppButton
              variant="primary"
              @click="router.push({ name: 'report-form' })"
            >
              <AppIcon
                name="plus"
                :size="16"
              />
              新建上报
            </AppButton>
          </div>
        </AppCard>
      </div>

      <div
        v-else
        class="drafts-page__list"
      >
        <AppCard
          v-for="d in drafts"
          :key="d.draft_id"
          padding="md"
          class="drafts-page__item"
        >
          <div class="drafts-page__item-header">
            <h3 class="drafts-page__item-title">
              {{ d.title || '(未命名草稿)' }}
            </h3>
            <span
              class="drafts-page__expires"
              :class="{ 'drafts-page__expires--urgent': daysLeft(d.expires_at) <= 3 }"
            >
              <AppIcon
                name="clock"
                :size="12"
              />
              {{ daysLeft(d.expires_at) }} 天后过期
            </span>
          </div>

          <div class="drafts-page__item-meta">
            <span v-if="d.fraud_type_id">
              <AppIcon
                name="tag"
                :size="12"
              />
              诈骗类型 #{{ d.fraud_type_id }}
            </span>
            <span v-if="d.incident_date">
              <AppIcon
                name="calendar"
                :size="12"
              />
              {{ d.incident_date }}
            </span>
            <span v-if="d.evidence_count > 0">
              <AppIcon
                name="image"
                :size="12"
              />
              {{ d.evidence_count }} 张证据
            </span>
            <span>
              <AppIcon
                name="edit"
                :size="12"
              />
              最近修改 {{ formatDate(d.updated_at) }}
            </span>
          </div>

          <p
            v-if="d.description"
            class="drafts-page__item-desc"
          >
            {{ d.description.slice(0, 100) }}{{ d.description.length > 100 ? '…' : '' }}
          </p>

          <div class="drafts-page__item-actions">
            <AppButton
              variant="primary"
              size="sm"
              @click="router.push({ name: 'report-form', query: { draft_id: d.draft_id } })"
            >
              <AppIcon
                name="edit"
                :size="14"
              />
              继续编辑
            </AppButton>
            <AppButton
              variant="ghost"
              size="sm"
              :loading="deletingId === d.draft_id"
              @click="deleteDraft(d.draft_id)"
            >
              <AppIcon
                name="trash-2"
                :size="14"
              />
              删除
            </AppButton>
          </div>
        </AppCard>
      </div>
    </template>
  </div>
</template>

<style scoped>
.drafts-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.drafts-page__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

.drafts-page__empty-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6);
  color: var(--color-text-secondary);
}

.drafts-page__empty-inner svg {
  color: var(--color-border-strong);
}

.drafts-page__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.drafts-page__item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.drafts-page__item-title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.drafts-page__expires {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.drafts-page__expires--urgent {
  color: var(--color-warning);
  font-weight: var(--font-weight-medium);
}

.drafts-page__item-meta {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.drafts-page__item-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.drafts-page__item-desc {
  margin: 0 0 var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.drafts-page__item-actions {
  display: flex;
  gap: var(--space-2);
}

.spin { animation: spin 1s linear infinite; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
