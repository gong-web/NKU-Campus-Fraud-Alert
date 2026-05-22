<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  warningsApi,
  WARNING_LEVEL_LABEL,
  WARNING_SCOPE_LABEL,
  WARNING_STATUS_LABEL,
  type WarningLevel,
  type WarningOut,
} from "@/api/warnings";
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

const loading = ref(false);
const errored = ref(false);
const errorMsg = ref("");
const warning = ref<WarningOut | null>(null);

const isOnline = computed<boolean>(() => warning.value?.status === "ONLINE");

function warnLevelClass(level: WarningLevel): "info" | "warning" | "urgent" {
  if (level === 3) return "urgent";
  if (level === 2) return "warning";
  return "info";
}

function formatDateTime(d: string | null | undefined): string {
  if (!d) return "—";
  return d.slice(0, 16).replace("T", " ");
}

async function load(): Promise<void> {
  const warningId = String(route.params.warning_id ?? "");
  if (!warningId) {
    errored.value = true;
    errorMsg.value = "缺少预警编号";
    return;
  }
  loading.value = true;
  errored.value = false;
  errorMsg.value = "";
  try {
    warning.value = await warningsApi.getAdmin(warningId);
  } catch (e) {
    errored.value = true;
    errorMsg.value = e instanceof ApiError ? e.message : "加载失败";
    warning.value = null;
  } finally {
    loading.value = false;
  }
}

async function appendNotice(): Promise<void> {
  if (!warning.value || !isOnline.value) return;
  try {
    const { value } = await ElMessageBox.prompt(
      "追加内容（≥5 字）",
      `追加说明 · ${warning.value.title}`,
      {
        confirmButtonText: "提交追加",
        cancelButtonText: "取消",
        inputType: "textarea",
        inputValidator: (v: string) =>
          (v?.trim().length ?? 0) >= 5 || "追加内容至少 5 字",
      },
    );
    await warningsApi.append(warning.value.warning_id, {
      appendix: String(value).trim(),
    });
    ElMessage.success("追加说明已提交");
    await load();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

async function offlineNotice(): Promise<void> {
  if (!warning.value || !isOnline.value) return;
  try {
    const { value } = await ElMessageBox.prompt(
      "下线原因（≥5 字）",
      `手动下线 · ${warning.value.title}`,
      {
        confirmButtonText: "确认下线",
        cancelButtonText: "取消",
        confirmButtonClass: "el-button--danger",
        inputType: "textarea",
        inputValidator: (v: string) =>
          (v?.trim().length ?? 0) >= 5 || "下线原因至少 5 字",
      },
    );
    await warningsApi.offline(warning.value.warning_id, {
      reason: String(value).trim(),
    });
    ElMessage.success("已下线");
    await load();
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    if (e instanceof ApiError) ElMessage.error(e.message);
  }
}

function goBack(): void {
  void router.push({ name: "admin-warning-list" });
}

onMounted(load);
</script>

<template>
  <div class="admin-warning-detail">
    <AppPageHeader badge="UC-07" title="预警详情" subtitle="管理员视角，含浏览量统计">
      <template #actions>
        <AppButton variant="ghost" size="sm" @click="goBack">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
        <AppButton
          variant="primary"
          size="sm"
          :disabled="!isOnline"
          @click="appendNotice"
        >
          <AppIcon name="edit" :size="13" />
          追加说明
        </AppButton>
        <AppButton
          variant="danger"
          size="sm"
          :disabled="!isOnline"
          @click="offlineNotice"
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
      <template v-else-if="warning">
        <AppCard padding="lg">
          <div class="admin-warning-detail__hero-tags">
            <AppStatusTag
              :status="'info'"
              :warn-level="warnLevelClass(warning.warning_level)"
              :text="`${WARNING_LEVEL_LABEL[warning.warning_level]}级`"
            />
            <AppStatusTag
              :status="warning.status === 'ONLINE' ? 'success' : 'neutral'"
              :text="WARNING_STATUS_LABEL[warning.status] ?? warning.status"
            />
            <span class="admin-warning-detail__chip">
              <AppIcon name="users" :size="12" />
              {{ WARNING_SCOPE_LABEL[warning.push_scope] ?? warning.push_scope }}
            </span>
          </div>
          <h2 class="admin-warning-detail__title">{{ warning.title }}</h2>
          <div class="admin-warning-detail__meta">
            <span class="admin-warning-detail__meta-cell">
              <AppIcon name="user" :size="13" />
              发布人：{{ warning.publisher_name || "—" }}
            </span>
            <span class="admin-warning-detail__meta-cell">
              <AppIcon name="clock" :size="13" />
              发布于 {{ formatDateTime(warning.published_at) }}
            </span>
            <span v-if="warning.expires_at" class="admin-warning-detail__meta-cell">
              <AppIcon name="calendar" :size="13" />
              失效于 {{ formatDateTime(warning.expires_at) }}
            </span>
            <span
              v-if="warning.target_dept_ids.length > 0"
              class="admin-warning-detail__meta-cell"
            >
              <AppIcon name="users" :size="13" />
              目标院系 {{ warning.target_dept_ids.length }} 个
            </span>
          </div>
        </AppCard>

        <AppCard padding="lg">
          <template #header>
            <div>
              <h3>预警正文</h3>
              <small>面向学生端展示</small>
            </div>
          </template>
          <div class="admin-warning-detail__content">{{ warning.content }}</div>
        </AppCard>

        <AppCard v-if="warning.appendix" padding="lg">
          <template #header>
            <div>
              <h3>追加说明</h3>
              <small>发布后补充的最新信息</small>
            </div>
          </template>
          <div class="admin-warning-detail__content admin-warning-detail__content--appendix">
            {{ warning.appendix }}
          </div>
        </AppCard>

        <AppCard v-if="warning.related_case_no" padding="md">
          <div class="admin-warning-detail__related">
            <AppIcon name="file-text" :size="14" />
            <span>关联案件编号</span>
            <code>{{ warning.related_case_no }}</code>
          </div>
        </AppCard>

        <AppCard v-if="warning.status === 'OFFLINE'" padding="md">
          <div class="admin-warning-detail__offline-block">
            <AppIcon name="info" :size="14" />
            <div>
              <strong>该预警已于 {{ formatDateTime(warning.offline_at) }} 下线</strong>
              <p v-if="warning.offline_reason">{{ warning.offline_reason }}</p>
            </div>
          </div>
        </AppCard>
      </template>
    </template>
  </div>
</template>

<style scoped>
.admin-warning-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-warning-detail__hero-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.admin-warning-detail__chip {
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

.admin-warning-detail__title {
  margin: 0 0 var(--space-3);
  font-family: var(--font-family-serif);
  font-size: clamp(20px, 2.4vw, 30px);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.admin-warning-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-4);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-warning-detail__meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.admin-warning-detail__content {
  font-size: var(--font-size-sm);
  line-height: 1.85;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}

.admin-warning-detail__content--appendix {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(239 108 0 / 4%);
  border-left: 3px solid var(--color-warning);
}

.admin-warning-detail__related {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.admin-warning-detail__related code {
  font-family: var(--font-family-mono);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.admin-warning-detail__offline-block {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  color: var(--color-text-secondary);
}

.admin-warning-detail__offline-block strong {
  display: block;
  color: var(--color-text-strong);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.admin-warning-detail__offline-block p {
  margin: 4px 0 0;
  font-size: var(--font-size-xs);
  line-height: 1.6;
}
</style>
