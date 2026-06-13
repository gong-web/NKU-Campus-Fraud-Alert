<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { EvidenceFileOut, FraudType, ReportCreateIn } from "@/api/reports";
import { reportsApi } from "@/api/reports";
import { AppButton, AppCard, AppIcon, AppPageHeader } from "@/components";

const router = useRouter();
const route = useRoute();

interface SavedEvidenceItem extends EvidenceFileOut {
  preview_url: string | null;
}

interface PendingEvidenceItem {
  local_id: string;
  file: File;
  preview_url: string | null;
}

// ── State ────────────────────────────────────────────────────────
const fraudTypes = ref<FraudType[]>([]);
const loading = ref(false);
const submitLoading = ref(false);
const draftLoading = ref(false);
const errorMsg = ref("");
const currentDraftId = ref<string | null>(null);
const submitAttempted = ref(false);
const titleInput = ref<HTMLInputElement | null>(null);
const fraudTypeSelect = ref<HTMLSelectElement | null>(null);
const incidentDateInput = ref<HTMLInputElement | null>(null);
const descriptionInput = ref<HTMLTextAreaElement | null>(null);

const form = ref<ReportCreateIn>({
  title: "",
  description: "",
  fraud_type_id: 0,
  incident_date: "",
  amount: null,
  fraud_method: null,
  is_anonymous: false,
  contact_way: null,
});

const pendingFiles = ref<PendingEvidenceItem[]>([]);
const savedEvidence = ref<SavedEvidenceItem[]>([]);

// ── Computed ─────────────────────────────────────────────────────
const descLength = computed(() => form.value.description.length);
const titleLength = computed(() => form.value.title.trim().length);
const descTone = computed(() => {
  if (descLength.value >= 200) return "success";
  if (descLength.value >= 50) return "warning";
  return "normal";
});

const titleError = computed(() => {
  if (titleLength.value === 0) return submitAttempted.value ? "请输入标题" : "";
  if (titleLength.value < 2) return `标题至少 2 个字，还需 ${2 - titleLength.value} 个字`;
  return "";
});

const fraudTypeError = computed(() =>
  submitAttempted.value && form.value.fraud_type_id <= 0 ? "请选择诈骗类型" : "",
);

const incidentDateError = computed(() =>
  submitAttempted.value && !form.value.incident_date ? "请选择事发日期" : "",
);

const descriptionError = computed(() => {
  const length = form.value.description.trim().length;
  if (length === 0) return submitAttempted.value ? "请输入事件经过" : "";
  if (length < 10) return `经过描述至少 10 个字，还需 ${10 - length} 个字`;
  return "";
});

const validationIssues = computed<string[]>(() => {
  const issues: string[] = [];
  if (titleLength.value < 2) issues.push(titleError.value || "标题至少 2 个字");
  if (form.value.fraud_type_id <= 0) issues.push("请选择诈骗类型");
  if (!form.value.incident_date) issues.push("请选择事发日期");
  if (form.value.description.trim().length < 10) {
    issues.push(descriptionError.value || "经过描述至少 10 个字");
  }
  return issues;
});

const isFormValid = computed(() => {
  return validationIssues.value.length === 0;
});

watch(validationIssues, (issues) => {
  if (!submitAttempted.value || !errorMsg.value.startsWith("暂时无法提交：")) return;
  errorMsg.value = issues.length ? `暂时无法提交：${issues.join("；")}` : "";
});

const totalEvidenceCount = computed(() => pendingFiles.value.length + savedEvidence.value.length);
const hasAnyEvidence = computed(() => totalEvidenceCount.value > 0);

// ── Lifecycle ────────────────────────────────────────────────────
onMounted(async () => {
  loading.value = true;
  try {
    fraudTypes.value = await reportsApi.listFraudTypes();

    const draftIdParam = route.query.draft_id;
    const draftId = Array.isArray(draftIdParam) ? draftIdParam[0] : draftIdParam;
    if (draftId && /^\d+$/.test(draftId)) {
      const draft = await reportsApi.getDraft(draftId);
      currentDraftId.value = draft.draft_id;
      form.value.title = draft.title ?? "";
      form.value.description = draft.description ?? "";
      form.value.fraud_type_id = draft.fraud_type_id ?? 0;
      form.value.incident_date = draft.incident_date ?? "";
      form.value.amount = draft.amount;
      form.value.fraud_method = draft.fraud_method;
      form.value.is_anonymous = draft.is_anonymous;
      form.value.contact_way = draft.contact_way;
      await hydrateSavedEvidence(draft.draft_id, draft.evidence_list ?? []);
    }
  } catch {
    errorMsg.value = "加载失败，请刷新页面重试";
  } finally {
    loading.value = false;
  }
});

onBeforeUnmount(() => {
  clearPendingPreviewUrls();
  clearSavedPreviewUrls();
});

// ── File Handling ─────────────────────────────────────────────────
function buildLocalId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function isImageMime(mimeType: string): boolean {
  return mimeType.startsWith("image/");
}

function clearPendingPreviewUrls(): void {
  for (const item of pendingFiles.value) {
    if (item.preview_url) URL.revokeObjectURL(item.preview_url);
  }
}

function clearSavedPreviewUrls(): void {
  for (const item of savedEvidence.value) {
    if (item.preview_url) URL.revokeObjectURL(item.preview_url);
  }
}

async function hydrateSavedEvidence(draftId: string, evidenceList: EvidenceFileOut[]): Promise<void> {
  clearSavedPreviewUrls();
  savedEvidence.value = evidenceList.map((item) => ({
    ...item,
    preview_url: null,
  }));

  await Promise.all(savedEvidence.value.map(async (item) => {
    if (!isImageMime(item.mime_type)) return;
    try {
      const blob = await reportsApi.getDraftEvidenceBlob(draftId, item.file_id);
      item.preview_url = URL.createObjectURL(blob);
    } catch {
      item.preview_url = null;
    }
  }));
}

function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  if (!input.files) return;

  for (const file of Array.from(input.files)) {
    if (totalEvidenceCount.value >= 10) {
      alert("最多上传 10 张图片");
      break;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert(`文件 ${file.name} 超过 5MB，已跳过`);
      continue;
    }
    pendingFiles.value.push({
      local_id: buildLocalId(),
      file,
      preview_url: isImageMime(file.type) ? URL.createObjectURL(file) : null,
    });
  }
  input.value = "";
}

function removePendingFile(index: number) {
  const item = pendingFiles.value[index];
  if (item?.preview_url) URL.revokeObjectURL(item.preview_url);
  pendingFiles.value.splice(index, 1);
}

async function removeSavedFile(fileId: string): Promise<void> {
  if (!currentDraftId.value) return;
  const item = savedEvidence.value.find((entry) => entry.file_id === fileId);
  if (!item) return;

  try {
    await reportsApi.deleteDraftEvidence(currentDraftId.value, fileId);
    if (item.preview_url) URL.revokeObjectURL(item.preview_url);
    savedEvidence.value = savedEvidence.value.filter((entry) => entry.file_id !== fileId);
  } catch {
    errorMsg.value = "删除草稿证据失败";
  }
}

// ── Submit ────────────────────────────────────────────────────────
async function focusFirstInvalidField(): Promise<void> {
  await nextTick();
  if (titleLength.value < 2) {
    titleInput.value?.focus();
    return;
  }
  if (form.value.fraud_type_id <= 0) {
    fraudTypeSelect.value?.focus();
    return;
  }
  if (!form.value.incident_date) {
    incidentDateInput.value?.focus();
    return;
  }
  descriptionInput.value?.focus();
}

async function submitReport() {
  submitAttempted.value = true;
  if (!isFormValid.value) {
    errorMsg.value = `暂时无法提交：${validationIssues.value.join("；")}`;
    await focusFirstInvalidField();
    return;
  }
  errorMsg.value = "";
  submitLoading.value = true;
  try {
    const result = await reportsApi.createReport(form.value);

    if (currentDraftId.value) {
      for (const item of savedEvidence.value) {
        const blob = await reportsApi.getDraftEvidenceBlob(currentDraftId.value, item.file_id);
        const file = new File([blob], item.original_name, {
          type: blob.type || item.mime_type || "application/octet-stream",
        });
        await reportsApi.uploadEvidence(result.case_id, file);
      }
    }

    // 上传证据图片
    for (const item of pendingFiles.value) {
      try {
        await reportsApi.uploadEvidence(result.case_id, item.file);
      } catch {
        // 证据上传失败不回滚，记录警告
        console.warn(`证据上传失败: ${item.file.name}`);
      }
    }

    // 提交成功后删除来源草稿
    if (currentDraftId.value) {
      try {
        await reportsApi.deleteDraft(currentDraftId.value);
      } catch {
        // 草稿删除失败不影响主流程
      }
    }

    await router.push({
      name: "report-success",
      query: { case_no: result.case_no, case_id: String(result.case_id) },
    });
  } catch (err: unknown) {
    const e = err as { message?: string };
    errorMsg.value = e.message || "提交失败，请稍后重试";
  } finally {
    submitLoading.value = false;
  }
}

async function saveDraft() {
  draftLoading.value = true;
  errorMsg.value = "";
  try {
    const payload = {
      title: form.value.title || null,
      description: form.value.description || null,
      fraud_type_id: form.value.fraud_type_id || null,
      incident_date: form.value.incident_date || null,
      amount: form.value.amount ?? null,
      fraud_method: form.value.fraud_method ?? null,
      is_anonymous: form.value.is_anonymous,
      contact_way: form.value.contact_way ?? null,
    };
    let draftId = currentDraftId.value;
    if (currentDraftId.value) {
      await reportsApi.updateDraft(currentDraftId.value, payload);
    } else {
      const draft = await reportsApi.createDraft(payload);
      currentDraftId.value = draft.draft_id;
      draftId = draft.draft_id;
    }

    if (draftId) {
      const stillPending: PendingEvidenceItem[] = [];
      for (const item of pendingFiles.value) {
        try {
          const saved = await reportsApi.uploadDraftEvidence(draftId, item.file);
          savedEvidence.value.push({
            ...saved,
            preview_url: item.preview_url,
          });
        } catch {
          stillPending.push(item);
        }
      }
      pendingFiles.value = stillPending;
    }
    alert("草稿已保存");
  } catch {
    errorMsg.value = "保存草稿失败";
  } finally {
    draftLoading.value = false;
  }
}
</script>

<template>
  <div class="report-form">
    <AppPageHeader
      title="我要上报疑似诈骗"
    />

    <div class="report-form__layout">
      <!-- 主表单 -->
      <AppCard
        padding="lg"
        class="report-form__main"
      >
        <div
          v-if="errorMsg"
          class="report-form__error"
        >
          <AppIcon
            name="alert-triangle"
            :size="16"
          />
          {{ errorMsg }}
        </div>

        <!-- 基本信息 -->
        <section class="report-form__section">
          <h3 class="report-form__section-title">基本信息</h3>

          <div class="report-form__field">
            <label class="report-form__label">
              标题
              <span class="required">*</span>
            </label>
            <input
              ref="titleInput"
              v-model="form.title"
              type="text"
              class="report-form__input"
              :class="{ 'report-form__input--error': Boolean(titleError) }"
              placeholder="一句话描述事件（2-200 字）"
              maxlength="200"
              :aria-invalid="Boolean(titleError)"
            >
            <div class="report-form__field-meta">
              <span
                v-if="titleError"
                class="report-form__field-error"
              >{{ titleError }}</span>
              <span v-else>{{ titleLength }} / 200 字</span>
            </div>
          </div>

          <div class="report-form__row">
            <div class="report-form__field">
              <label class="report-form__label">
                诈骗类型
                <span class="required">*</span>
              </label>
              <select
                ref="fraudTypeSelect"
                v-model="form.fraud_type_id"
                class="report-form__select"
                :class="{ 'report-form__input--error': Boolean(fraudTypeError) }"
                :disabled="loading"
                :aria-invalid="Boolean(fraudTypeError)"
              >
                <option
                  :value="0"
                  disabled
                >
                  请选择诈骗类型
                </option>
                <option
                  v-for="t in fraudTypes"
                  :key="t.type_id"
                  :value="t.type_id"
                >
                  {{ t.type_name }}
                </option>
              </select>
              <span
                v-if="fraudTypeError"
                class="report-form__field-error"
              >{{ fraudTypeError }}</span>
            </div>

            <div class="report-form__field">
              <label class="report-form__label">
                事发日期
                <span class="required">*</span>
              </label>
              <input
                ref="incidentDateInput"
                v-model="form.incident_date"
                type="date"
                class="report-form__input"
                :class="{ 'report-form__input--error': Boolean(incidentDateError) }"
                :max="new Date().toISOString().split('T')[0]"
                :aria-invalid="Boolean(incidentDateError)"
              >
              <span
                v-if="incidentDateError"
                class="report-form__field-error"
              >{{ incidentDateError }}</span>
            </div>
          </div>

          <div class="report-form__row">
            <div class="report-form__field">
              <label class="report-form__label">涉案金额（元，可选）</label>
              <input
                v-model.number="form.amount"
                type="number"
                class="report-form__input"
                placeholder="0.00"
                min="0"
                step="0.01"
              >
            </div>

            <div class="report-form__field">
              <label class="report-form__label">诈骗手法简述（可选）</label>
              <input
                v-model="form.fraud_method"
                type="text"
                class="report-form__input"
                placeholder="如：要求下载 APP、引导投资等"
                maxlength="200"
              >
            </div>
          </div>
        </section>

        <!-- 详细描述 -->
        <section class="report-form__section">
          <h3 class="report-form__section-title">事件详细描述</h3>
          <div class="report-form__field">
            <label class="report-form__label">
              经过描述
              <span class="required">*</span>
            </label>
            <textarea
              ref="descriptionInput"
              v-model="form.description"
              class="report-form__textarea"
              :class="{ 'report-form__input--error': Boolean(descriptionError) }"
              placeholder="请详细描述事件经过，包括时间、地点、对方说了什么、您做了什么等（建议 200 字以上）"
              rows="8"
              maxlength="5000"
              :aria-invalid="Boolean(descriptionError)"
            />
            <div
              class="report-form__char-count"
              :class="`report-form__char-count--${descTone}`"
            >
              <span
                v-if="descriptionError"
                class="report-form__field-error"
              >{{ descriptionError }}</span>
              <span v-else>{{ descLength }} / 5000 字</span>
            </div>
          </div>
        </section>

        <!-- 证据上传 -->
        <section class="report-form__section">
          <h3 class="report-form__section-title">
            证据图片
            <small>（可选，最多 10 张，每张 ≤ 5 MB）</small>
          </h3>

          <div class="report-form__upload-zone">
            <label
              class="report-form__upload-btn"
              :class="{ 'disabled': totalEvidenceCount >= 10 }"
            >
              <AppIcon
                name="upload"
                :size="18"
              />
              <span>点击上传图片</span>
              <input
                type="file"
                accept="image/*,.pdf"
                multiple
                style="display:none"
                :disabled="totalEvidenceCount >= 10"
                @change="handleFileChange"
              >
            </label>

            <div
              v-if="hasAnyEvidence"
              class="report-form__previews"
            >
              <div
                v-for="item in savedEvidence"
                :key="`saved-${item.file_id}`"
                class="report-form__preview-item"
              >
                <img
                  v-if="item.preview_url"
                  :src="item.preview_url"
                  :alt="item.original_name"
                  class="report-form__preview-img"
                >
                <div
                  v-else
                  class="report-form__preview-placeholder"
                >
                  <AppIcon
                    name="file-text"
                    :size="20"
                  />
                </div>
                <button
                  type="button"
                  class="report-form__preview-remove"
                  @click="removeSavedFile(item.file_id)"
                >
                  <AppIcon
                    name="x"
                    :size="12"
                  />
                </button>
                <span class="report-form__preview-name">{{ item.original_name }}</span>
              </div>

              <div
                v-for="(item, idx) in pendingFiles"
                :key="item.local_id"
                class="report-form__preview-item"
              >
                <img
                  v-if="item.preview_url"
                  :src="item.preview_url"
                  :alt="item.file.name"
                  class="report-form__preview-img"
                >
                <div
                  v-else
                  class="report-form__preview-placeholder"
                >
                  <AppIcon
                    name="file-text"
                    :size="20"
                  />
                </div>
                <button
                  type="button"
                  class="report-form__preview-remove"
                  @click="removePendingFile(idx)"
                >
                  <AppIcon
                    name="x"
                    :size="12"
                  />
                </button>
                <span class="report-form__preview-name">{{ item.file.name }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 隐私设置 -->
        <section class="report-form__section">
          <h3 class="report-form__section-title">隐私设置</h3>

          <label class="report-form__checkbox-label">
            <input
              v-model="form.is_anonymous"
              type="checkbox"
              class="report-form__checkbox"
            >
            <span>
              <strong>匿名上报</strong>
              <small>身份加密存储，审核员无法查看</small>
            </span>
          </label>

          <div
            v-if="!form.is_anonymous"
            class="report-form__field"
          >
            <label class="report-form__label">联系方式（可选）</label>
            <input
              v-model="form.contact_way"
              type="text"
              class="report-form__input"
              placeholder="方便审核员与您联系（手机号或邮箱）"
              maxlength="200"
            >
          </div>
        </section>

        <!-- 操作按钮 -->
        <div
          v-if="validationIssues.length"
          class="report-form__validation-summary"
          role="status"
        >
          <AppIcon name="info" :size="15" />
          <div>
            <strong>完成以下内容后即可提交</strong>
            <span>{{ validationIssues.join("；") }}</span>
          </div>
        </div>
        <div class="report-form__actions">
          <AppButton
            variant="ghost"
            :loading="draftLoading"
            @click="saveDraft"
          >
            <AppIcon
              name="save"
              :size="16"
            />
            保存草稿
          </AppButton>
          <AppButton
            variant="primary"
            :loading="submitLoading"
            :aria-label="isFormValid ? '提交上报' : `提交上报，当前还需：${validationIssues.join('；')}`"
            @click="submitReport"
          >
            <AppIcon
              name="send"
              :size="16"
            />
            提交上报
          </AppButton>
        </div>
      </AppCard>

      <aside class="report-form__tips">
        <p class="report-form__urgent">
          <AppIcon name="siren" :size="16" />
          涉及财产损失或人身安全，请立即拨打 <a href="tel:110">110</a>
        </p>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.report-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.report-form__layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
  align-items: start;
}

.report-form__section {
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-5);
}

.report-form__section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.report-form__section-title {
  margin: 0 0 var(--space-4);
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.report-form__section-title small {
  font-family: var(--font-family-sans);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-normal);
}

.report-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

@media (width <= 640px) {
  .report-form__row {
    grid-template-columns: 1fr;
  }
}

.report-form__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  margin-bottom: var(--space-4);
}

.report-form__field:last-child {
  margin-bottom: 0;
}

.report-form__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-strong);
}

.report-form__label .required {
  color: var(--color-danger);
  margin-left: 2px;
}

.report-form__input,
.report-form__select,
.report-form__textarea {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--font-size-sm);
  transition: border-color var(--duration-base) var(--easing-out);
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.report-form__input:focus,
.report-form__select:focus,
.report-form__textarea:focus {
  border-color: var(--color-brand-500);
  box-shadow: 0 0 0 3px rgb(134 38 51 / 10%);
}

.report-form__input--error {
  border-color: var(--color-danger);
  background: rgb(198 40 40 / 2%);
}

.report-form__input--error:focus {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 3px rgb(198 40 40 / 10%);
}

.report-form__field-meta {
  display: flex;
  justify-content: flex-end;
  min-height: 18px;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
}

.report-form__field-error {
  color: var(--color-danger);
  font-weight: var(--font-weight-medium);
}

.report-form__textarea {
  resize: vertical;
  line-height: 1.7;
}

.report-form__char-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  display: flex;
  gap: var(--space-2);
  align-items: center;
}

.report-form__char-count--success {
  color: var(--color-success);
}

.report-form__char-count--warning {
  color: var(--color-warning);
}

.report-form__char-ok {
  color: var(--color-success);
  font-weight: var(--font-weight-medium);
}

/* Upload zone */
.report-form__upload-zone {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.report-form__upload-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1.5px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  transition: all var(--duration-base) var(--easing-out);
  width: fit-content;
}

.report-form__upload-btn:hover:not(.disabled) {
  border-color: var(--color-brand-500);
  color: var(--color-brand-600);
  background: var(--color-brand-50);
}

.report-form__upload-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.report-form__previews {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.report-form__preview-item {
  position: relative;
  width: 88px;
}

.report-form__preview-img {
  width: 88px;
  height: 88px;
  object-fit: cover;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.report-form__preview-placeholder {
  width: 88px;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-soft);
  color: var(--color-text-secondary);
}

.report-form__preview-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgb(0 0 0 / 60%);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.report-form__preview-name {
  display: block;
  font-size: 10px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 4px;
}

.report-form__preview-tag {
  display: inline-block;
  margin-top: 4px;
  font-size: 10px;
  color: var(--color-success);
}

.report-form__preview-tag--pending {
  color: var(--color-warning);
}

/* Checkbox */
.report-form__checkbox-label {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  cursor: pointer;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-3);
  transition: all var(--duration-base);
}

.report-form__checkbox-label:hover {
  border-color: var(--color-brand-400);
  background: var(--color-brand-50);
}

.report-form__checkbox {
  margin-top: 3px;
  flex-shrink: 0;
}

.report-form__checkbox-label span {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.report-form__checkbox-label strong {
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
}

.report-form__checkbox-label small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* Actions */
.report-form__validation-summary {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1px solid rgb(197 123 0 / 24%);
  border-radius: var(--radius-md);
  background: rgb(197 123 0 / 6%);
  color: var(--color-warning);
  font-size: var(--font-size-xs);
  line-height: 1.6;
}

.report-form__validation-summary > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.report-form__validation-summary strong {
  color: var(--color-text-strong);
  font-size: var(--font-size-sm);
}

.report-form__validation-summary span {
  color: var(--color-text-secondary);
}

.report-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

/* Error */
.report-form__error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(198 40 40 / 8%);
  border: 1px solid rgb(198 40 40 / 24%);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
  margin-bottom: var(--space-4);
}

.report-form__tips {
  margin-top: var(--space-2);
}

.report-form__urgent {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(198 40 40 / 6%);
  border: 1px solid rgb(198 40 40 / 18%);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.report-form__urgent a {
  color: var(--color-danger);
  font-weight: var(--font-weight-semibold);
}
</style>
