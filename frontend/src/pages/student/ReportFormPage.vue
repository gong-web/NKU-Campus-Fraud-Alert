<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { FraudType, ReportCreateIn } from "@/api/reports";
import { reportsApi } from "@/api/reports";
import { AppButton, AppCard, AppIcon, AppPageHeader } from "@/components";

const router = useRouter();
const route = useRoute();

// ── State ────────────────────────────────────────────────────────
const fraudTypes = ref<FraudType[]>([]);
const loading = ref(false);
const submitLoading = ref(false);
const draftLoading = ref(false);
const errorMsg = ref("");
const currentDraftId = ref<number | null>(null);

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

const pendingFiles = ref<File[]>([]);
const filePreviews = ref<string[]>([]);

// ── Computed ─────────────────────────────────────────────────────
const descLength = computed(() => form.value.description.length);
const descTone = computed(() => {
  if (descLength.value >= 200) return "success";
  if (descLength.value >= 50) return "warning";
  return "normal";
});

const isFormValid = computed(() => {
  return (
    form.value.title.trim().length >= 2 &&
    form.value.description.trim().length >= 10 &&
    form.value.fraud_type_id > 0 &&
    form.value.incident_date !== ""
  );
});

// ── Lifecycle ────────────────────────────────────────────────────
onMounted(async () => {
  loading.value = true;
  try {
    fraudTypes.value = await reportsApi.listFraudTypes();

    const draftIdParam = route.query.draft_id;
    if (draftIdParam) {
      const draftId = Number(draftIdParam);
      if (!Number.isNaN(draftId) && draftId > 0) {
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
      }
    }
  } catch {
    errorMsg.value = "加载失败，请刷新页面重试";
  } finally {
    loading.value = false;
  }
});

// ── File Handling ─────────────────────────────────────────────────
function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  if (!input.files) return;

  for (const file of Array.from(input.files)) {
    if (pendingFiles.value.length >= 10) {
      alert("最多上传 10 张图片");
      break;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert(`文件 ${file.name} 超过 5MB，已跳过`);
      continue;
    }
    pendingFiles.value.push(file);
    const url = URL.createObjectURL(file);
    filePreviews.value.push(url);
  }
  input.value = "";
}

function removeFile(index: number) {
  const url = filePreviews.value[index];
  if (url) URL.revokeObjectURL(url);
  pendingFiles.value.splice(index, 1);
  filePreviews.value.splice(index, 1);
}

// ── Submit ────────────────────────────────────────────────────────
async function submitReport() {
  if (!isFormValid.value) return;
  errorMsg.value = "";
  submitLoading.value = true;
  try {
    const result = await reportsApi.createReport(form.value);

    // 上传证据图片
    for (const file of pendingFiles.value) {
      try {
        await reportsApi.uploadEvidence(result.case_id, file);
      } catch {
        // 证据上传失败不回滚，记录警告
        console.warn(`证据上传失败: ${file.name}`);
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
    if (currentDraftId.value) {
      await reportsApi.updateDraft(currentDraftId.value, payload);
    } else {
      const draft = await reportsApi.createDraft(payload);
      currentDraftId.value = draft.draft_id;
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
      badge="上报 · UC-01"
      title="我要上报疑似诈骗"
      subtitle="请如实描述事件经过。个人信息全程加密，可选择匿名上报。"
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
              v-model="form.title"
              type="text"
              class="report-form__input"
              placeholder="一句话描述事件（2-200 字）"
              maxlength="200"
            >
          </div>

          <div class="report-form__row">
            <div class="report-form__field">
              <label class="report-form__label">
                诈骗类型
                <span class="required">*</span>
              </label>
              <select
                v-model="form.fraud_type_id"
                class="report-form__select"
                :disabled="loading"
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
            </div>

            <div class="report-form__field">
              <label class="report-form__label">
                事发日期
                <span class="required">*</span>
              </label>
              <input
                v-model="form.incident_date"
                type="date"
                class="report-form__input"
                :max="new Date().toISOString().split('T')[0]"
              >
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
              v-model="form.description"
              class="report-form__textarea"
              placeholder="请详细描述事件经过，包括时间、地点、对方说了什么、您做了什么等（建议 200 字以上）"
              rows="8"
              maxlength="5000"
            />
            <div
              class="report-form__char-count"
              :class="`report-form__char-count--${descTone}`"
            >
              <span>已输入 {{ descLength }} 字</span>
              <span
                v-if="descLength < 200"
                class="report-form__char-hint"
              >（建议至少 200 字，有助于审核）</span>
              <span
                v-else
                class="report-form__char-ok"
              >✓ 字数充分</span>
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
              :class="{ 'disabled': pendingFiles.length >= 10 }"
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
                :disabled="pendingFiles.length >= 10"
                @change="handleFileChange"
              >
            </label>

            <div
              v-if="pendingFiles.length > 0"
              class="report-form__previews"
            >
              <div
                v-for="(url, idx) in filePreviews"
                :key="idx"
                class="report-form__preview-item"
              >
                <img
                  :src="url"
                  :alt="pendingFiles[idx]?.name ?? ''"
                  class="report-form__preview-img"
                >
                <button
                  type="button"
                  class="report-form__preview-remove"
                  @click="removeFile(idx)"
                >
                  <AppIcon
                    name="x"
                    :size="12"
                  />
                </button>
                <span class="report-form__preview-name">{{ pendingFiles[idx]?.name ?? '' }}</span>
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
              <small>您的真实姓名与学号将加密存储，仅司法授权场景可解密，普通审核员看不到您的身份</small>
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
            :disabled="!isFormValid"
            :loading="submitLoading"
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

      <!-- 侧边提示 -->
      <aside class="report-form__tips">
        <AppCard padding="md">
          <template #header>
            <div class="report-form__tips-title">
              <AppIcon
                name="info"
                :size="16"
              />
              填写提示
            </div>
          </template>
          <ul class="report-form__tips-list">
            <li>
              <AppIcon
                name="shield-check"
                :size="14"
              />
              实名信息加密存储，仅司法授权下可解密
            </li>
            <li>
              <AppIcon
                name="clock"
                :size="14"
              />
              提交后 24 小时内会有审核员处理
            </li>
            <li>
              <AppIcon
                name="bell"
                :size="14"
              />
              状态变更时会收到站内通知
            </li>
            <li>
              <AppIcon
                name="file-text"
                :size="14"
              />
              描述越详细，处理越高效
            </li>
          </ul>
        </AppCard>

        <AppCard
          padding="md"
          class="report-form__urgent-card"
        >
          <p class="report-form__urgent">
            <AppIcon
              name="siren"
              :size="16"
            />
            <strong>如财产损失较大或人身安全受威胁，请立即拨打 110 报警！</strong>
          </p>
        </AppCard>
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
  grid-template-columns: 1fr 280px;
  gap: var(--space-5);
  align-items: start;
}

@media (width <= 1024px) {
  .report-form__layout {
    grid-template-columns: 1fr;
  }
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

/* Urgent warning card */
.report-form__urgent-card {
  background: rgb(255 243 205 / 80%);
  border-color: rgb(230 162 0 / 30%);
}

/* Tips sidebar */
.report-form__tips {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  position: sticky;
  top: 80px;
}

.report-form__tips-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.report-form__tips-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.report-form__tips-list li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.report-form__tips-list li svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--color-brand-500);
}

.report-form__urgent {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  margin: 0;
  font-size: var(--font-size-xs);
  line-height: 1.6;
}
</style>
