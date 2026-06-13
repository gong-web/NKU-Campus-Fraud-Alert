<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { useAuthStore } from "@/stores/auth";
import {
  knowledgeApi,
  KNOWLEDGE_REVIEW_ACTION_LABEL,
  KNOWLEDGE_SOURCE_LABEL,
  KNOWLEDGE_STATUS_LABEL,
  KNOWLEDGE_STATUS_TONE,
  type KnowledgeHistoryItem,
  type KnowledgeOut,
} from "@/api/knowledge";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppErrorState,
  AppIcon,
  AppPageHeader,
  AppSkeleton,
  AppStatusTag,
} from "@/components";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const errored = ref(false);
const errorMsg = ref("");
const entry = ref<KnowledgeOut | null>(null);
const history = ref<KnowledgeHistoryItem[]>([]);
const historyLoading = ref(false);

const isAuthor = computed<boolean>(() => {
  return Boolean(
    entry.value &&
      auth.me?.user_id != null &&
      entry.value.author_id === auth.me.user_id,
  );
});

const canReview = computed<boolean>(() => auth.hasPermission("kb:review"));
const canOffline = computed<boolean>(() => auth.hasPermission("kb:offline"));

const status = computed<string>(() => entry.value?.status ?? "");

function formatDateTime(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 19).replace("T", " ");
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
    entry.value = await knowledgeApi.getAdmin(entryId);
  } catch (e) {
    errored.value = true;
    errorMsg.value = e instanceof ApiError ? e.message : "加载失败";
    entry.value = null;
  } finally {
    loading.value = false;
  }
}

async function loadHistory(): Promise<void> {
  if (!entry.value) return;
  historyLoading.value = true;
  try {
    history.value = await knowledgeApi.history(entry.value.entry_id);
  } catch {
    history.value = [];
  } finally {
    historyLoading.value = false;
  }
}

function goEdit(): void {
  if (!entry.value) return;
  void router.push({
    name: "admin-kb-edit",
    params: { entry_id: entry.value.entry_id },
  });
}

async function submitForReview(): Promise<void> {
  if (!entry.value || entry.value.status !== "DRAFT") return;
  try {
    await ElMessageBox.confirm(
      `确定将《${entry.value.title}》提交校级审核？`,
      "提交审核",
      { confirmButtonText: "提交", cancelButtonText: "取消" },
    );
    await knowledgeApi.submit(entry.value.entry_id);
    ElMessage.success("已提交审核");
    await load();
    await loadHistory();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

async function approve(): Promise<void> {
  if (!entry.value || entry.value.status !== "PENDING") return;
  try {
    const { value } = await ElMessageBox.prompt(
      "可填写审核备注（可选）",
      `通过发布 · ${entry.value.title}`,
      {
        confirmButtonText: "通过发布",
        cancelButtonText: "取消",
        inputType: "textarea",
        inputValidator: () => true,
      },
    );
    await knowledgeApi.review(entry.value.entry_id, {
      action: "APPROVE",
      ...(String(value ?? "").trim() ? { review_note: String(value).trim() } : {}),
    });
    ElMessage.success("已通过发布");
    await load();
    await loadHistory();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

async function reject(): Promise<void> {
  if (!entry.value || entry.value.status !== "PENDING") return;
  try {
    const { value } = await ElMessageBox.prompt(
      "驳回原因（将退回作者修改）",
      `驳回回草稿 · ${entry.value.title}`,
      {
        confirmButtonText: "确认驳回",
        cancelButtonText: "取消",
        confirmButtonClass: "el-button--danger",
        inputType: "textarea",
        inputValidator: (v: string) =>
          (v?.trim().length ?? 0) >= 1 || "请填写驳回原因",
      },
    );
    await knowledgeApi.review(entry.value.entry_id, {
      action: "REJECT",
      review_note: String(value).trim(),
    });
    ElMessage.success("已驳回");
    await load();
    await loadHistory();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

async function offlineEntry(): Promise<void> {
  if (!entry.value || entry.value.status !== "PUBLISHED") return;
  try {
    const { value } = await ElMessageBox.prompt(
      "下线原因",
      `下线 · ${entry.value.title}`,
      {
        confirmButtonText: "确认下线",
        cancelButtonText: "取消",
        confirmButtonClass: "el-button--danger",
        inputType: "textarea",
        inputValidator: (v: string) =>
          (v?.trim().length ?? 0) >= 1 || "请填写下线原因",
      },
    );
    await knowledgeApi.offline(entry.value.entry_id, {
      reason: String(value).trim(),
    });
    ElMessage.success("已下线");
    await load();
    await loadHistory();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

function goBack(): void {
  void router.push({ name: "admin-kb-list" });
}

function reviewActionLabel(action: string): string {
  return (
    KNOWLEDGE_REVIEW_ACTION_LABEL[action] ??
    {
      CREATE: "新建草稿",
      UPDATE: "编辑草稿",
      SUBMIT: "提交审核",
      OFFLINE: "下线",
    }[action] ??
    action
  );
}

onMounted(async () => {
  await load();
  if (entry.value) await loadHistory();
});
</script>

<template>
  <div class="admin-kb-detail">
    <AppPageHeader badge="UC-04 / UC-08" title="知识条目详情" subtitle="管理员视角，含状态、审核记录与历史版本">
      <template #actions>
        <AppButton variant="ghost" size="sm" @click="goBack">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
        <AppButton
          v-if="status === 'DRAFT' && isAuthor"
          variant="ghost"
          size="sm"
          @click="goEdit"
        >
          <AppIcon name="edit" :size="13" />
          编辑
        </AppButton>
        <AppButton
          v-if="status === 'DRAFT' && isAuthor"
          variant="primary"
          size="sm"
          @click="submitForReview"
        >
          <AppIcon name="send" :size="13" />
          提交审核
        </AppButton>
        <AppButton
          v-if="status === 'PENDING' && canReview"
          variant="primary"
          size="sm"
          @click="approve"
        >
          <AppIcon name="circle-check" :size="13" />
          通过发布
        </AppButton>
        <AppButton
          v-if="status === 'PENDING' && canReview"
          variant="danger"
          size="sm"
          @click="reject"
        >
          <AppIcon name="x" :size="13" />
          驳回
        </AppButton>
        <AppButton
          v-if="status === 'PUBLISHED' && canOffline"
          variant="danger"
          size="sm"
          @click="offlineEntry"
        >
          <AppIcon name="x" :size="13" />
          下线
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
        <AppSkeleton :rows="6" />
      </AppCard>
      <template v-else-if="entry">
        <AppCard padding="lg">
          <div class="admin-kb-detail__hero-tags">
            <AppStatusTag
              :status="KNOWLEDGE_STATUS_TONE[entry.status] ?? 'neutral'"
              :text="KNOWLEDGE_STATUS_LABEL[entry.status] ?? entry.status"
            />
            <span class="admin-kb-detail__chip">
              <AppIcon name="tag" :size="12" />
              {{ entry.fraud_type_name || "通用" }}
            </span>
            <span class="admin-kb-detail__chip">
              <AppIcon name="info" :size="12" />
              {{ KNOWLEDGE_SOURCE_LABEL[entry.source_type] ?? entry.source_type }}
            </span>
            <span class="admin-kb-detail__chip admin-kb-detail__chip--ver">
              v{{ entry.version }}
            </span>
          </div>
          <h2 class="admin-kb-detail__title">{{ entry.title }}</h2>
          <div class="admin-kb-detail__meta">
            <span class="admin-kb-detail__meta-cell">
              <AppIcon name="user" :size="13" />
              作者：{{ entry.author_name || "—" }}
            </span>
            <span class="admin-kb-detail__meta-cell">
              <AppIcon name="clock" :size="13" />
              创建于 {{ formatDateTime(entry.created_at) }}
            </span>
            <span class="admin-kb-detail__meta-cell">
              <AppIcon name="clock" :size="13" />
              更新于 {{ formatDateTime(entry.updated_at) }}
            </span>
            <span v-if="entry.published_at" class="admin-kb-detail__meta-cell">
              <AppIcon name="circle-check" :size="13" />
              发布于 {{ formatDateTime(entry.published_at) }}
            </span>
            <span v-if="entry.peak_periods" class="admin-kb-detail__meta-cell">
              <AppIcon name="calendar" :size="13" />
              高发期 · {{ entry.peak_periods }}
            </span>
          </div>
        </AppCard>

        <AppCard
          v-if="entry.review_note"
          padding="md"
        >
          <div class="admin-kb-detail__review-note">
            <AppIcon name="info" :size="14" />
            <div>
              <strong>审核备注</strong>
              <p>{{ entry.review_note }}</p>
              <span v-if="entry.reviewer_name">
                审核人：{{ entry.reviewer_name }}
              </span>
            </div>
          </div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>案情概要</h3>
              <small>已脱敏处理，发布后即学生端摘要</small>
            </div>
          </template>
          <div class="admin-kb-detail__content">{{ entry.desensitized_summary }}</div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>识别要点</h3>
              <small>面向学生展示，请保证条目化与可读性</small>
            </div>
          </template>
          <div class="admin-kb-detail__content admin-kb-detail__content--accent">
            {{ entry.identification_points }}
          </div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>防范建议</h3>
              <small>建议给出可立即执行的步骤</small>
            </div>
          </template>
          <div class="admin-kb-detail__content">{{ entry.prevention_advice }}</div>
        </AppCard>

        <AppCard v-if="entry.source_reference" padding="md">
          <div class="admin-kb-detail__source">
            <AppIcon name="file-text" :size="14" />
            <span>来源参考</span>
            <span class="admin-kb-detail__source-text">{{ entry.source_reference }}</span>
          </div>
        </AppCard>

        <AppCard v-if="entry.status === 'OFFLINE' && entry.offlined_at" padding="md">
          <div class="admin-kb-detail__offline-block">
            <AppIcon name="info" :size="14" />
            <div>
              <strong>该条目已于 {{ formatDateTime(entry.offlined_at) }} 下线</strong>
            </div>
          </div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>历史版本（事件溯源）</h3>
              <small>记录每次状态变更与编辑操作</small>
            </div>
          </template>
          <div v-if="historyLoading" class="admin-kb-detail__history-loading">
            <AppIcon name="loader" :size="18" class="admin-kb-detail__spin" />
            正在加载历史…
          </div>
          <div v-else-if="history.length === 0" class="admin-kb-detail__history-empty">
            尚无历史记录
          </div>
          <ol v-else class="admin-kb-detail__history">
            <li
              v-for="h in history"
              :key="h.history_id"
              class="admin-kb-detail__history-item"
            >
              <span class="admin-kb-detail__history-ver">v{{ h.version }}</span>
              <div class="admin-kb-detail__history-body">
                <div class="admin-kb-detail__history-action">
                  {{ reviewActionLabel(h.action) }}
                </div>
                <div class="admin-kb-detail__history-meta">
                  <span>
                    <AppIcon name="user" :size="11" />
                    {{ h.modified_by }}
                  </span>
                  <span>
                    <AppIcon name="clock" :size="11" />
                    {{ formatDateTime(h.modified_at) }}
                  </span>
                </div>
              </div>
            </li>
          </ol>
        </AppCard>
      </template>
    </template>
  </div>
</template>

<style scoped>
.admin-kb-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-kb-detail__hero-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.admin-kb-detail__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-bg-soft);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: var(--font-weight-medium);
}

.admin-kb-detail__chip--ver {
  font-family: var(--font-family-mono);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  border-color: transparent;
}

.admin-kb-detail__title {
  margin: 0 0 var(--space-3);
  font-family: var(--font-family-serif);
  font-size: clamp(20px, 2.4vw, 30px);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.admin-kb-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-4);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-kb-detail__meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.admin-kb-detail__content {
  font-size: var(--font-size-sm);
  line-height: 1.85;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}

.admin-kb-detail__content--accent {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(239 108 0 / 4%);
  border-left: 3px solid var(--color-warning);
}

.admin-kb-detail__source {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.admin-kb-detail__source-text {
  font-family: var(--font-family-mono);
  background: var(--color-bg-soft);
  border: 1px solid var(--color-border);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  color: var(--color-text);
  word-break: break-all;
}

.admin-kb-detail__review-note {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: rgb(239 108 0 / 6%);
  border-left: 3px solid var(--color-warning);
  border-radius: var(--radius-md);
  color: var(--color-text);
}

.admin-kb-detail__review-note strong {
  display: block;
  color: var(--color-text-strong);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.admin-kb-detail__review-note p {
  margin: 4px 0;
  font-size: var(--font-size-sm);
  line-height: 1.7;
  white-space: pre-wrap;
}

.admin-kb-detail__review-note span {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-kb-detail__offline-block {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  color: var(--color-text-secondary);
}

.admin-kb-detail__offline-block strong {
  display: block;
  color: var(--color-text-strong);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.admin-kb-detail__history-loading,
.admin-kb-detail__history-empty {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.admin-kb-detail__spin {
  animation: admin-kb-detail-spin 1s linear infinite;
}

@keyframes admin-kb-detail-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.admin-kb-detail__history {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.admin-kb-detail__history-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.admin-kb-detail__history-ver {
  flex-shrink: 0;
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  padding: 2px 10px;
  border-radius: var(--radius-pill);
}

.admin-kb-detail__history-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.admin-kb-detail__history-action {
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.admin-kb-detail__history-meta {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.admin-kb-detail__history-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
