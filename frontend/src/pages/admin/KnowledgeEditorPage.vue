<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { reportsApi } from "@/api/reports";
import type { FraudType } from "@/types/report";
import {
  knowledgeApi,
  type KnowledgeCreateBody,
  type KnowledgeOut,
  type KnowledgeSourceType,
  type KnowledgeUpdateBody,
} from "@/api/knowledge";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppErrorState,
  AppIcon,
  AppInput,
  AppPageHeader,
  AppSkeleton,
} from "@/components";

const route = useRoute();
const router = useRouter();

const isEditMode = computed<boolean>(() => Boolean(route.params.entry_id));
const entryId = computed<string>(() =>
  isEditMode.value ? String(route.params.entry_id) : "",
);

const loading = ref<boolean>(false);
const submitting = ref<boolean>(false);
const errored = ref<boolean>(false);
const errorMsg = ref<string>("");

const fraudTypes = ref<FraudType[]>([]);
const initial = ref<KnowledgeOut | null>(null);

interface FormState {
  title: string;
  fraud_type_id: number | null;
  desensitized_summary: string;
  identification_points: string;
  prevention_advice: string;
  peak_periods: string;
  source_type: KnowledgeSourceType;
  source_reference: string;
}

const form = reactive<FormState>({
  title: "",
  fraud_type_id: null,
  desensitized_summary: "",
  identification_points: "",
  prevention_advice: "",
  peak_periods: "",
  source_type: "CASE",
  source_reference: "",
});

const errors = reactive<{
  title: string;
  fraud_type_id: string;
  desensitized_summary: string;
  identification_points: string;
  prevention_advice: string;
}>({
  title: "",
  fraud_type_id: "",
  desensitized_summary: "",
  identification_points: "",
  prevention_advice: "",
});

const SOURCES: ReadonlyArray<{
  value: KnowledgeSourceType;
  label: string;
  desc: string;
}> = [
  { value: "CASE", label: "校内案件", desc: "源自本校真实上报案件" },
  { value: "SCHOOL", label: "校方公告", desc: "保卫处或学工处发布" },
  { value: "NATIONAL", label: "反诈中心", desc: "国家反诈中心权威发布" },
];

function selectSource(s: KnowledgeSourceType): void {
  form.source_type = s;
}

function selectFraudType(id: number): void {
  form.fraud_type_id = id;
  errors.fraud_type_id = "";
}

async function loadFraudTypes(): Promise<void> {
  try {
    fraudTypes.value = await reportsApi.listFraudTypes();
  } catch {
    fraudTypes.value = [];
  }
}

async function loadEntry(): Promise<void> {
  if (!isEditMode.value) return;
  loading.value = true;
  errored.value = false;
  errorMsg.value = "";
  try {
    const data = await knowledgeApi.getAdmin(entryId.value);
    initial.value = data;
    if (data.status !== "DRAFT") {
      ElMessage.warning("仅草稿状态可编辑，将跳转到详情");
      void router.replace({
        name: "admin-kb-detail",
        params: { entry_id: entryId.value },
      });
      return;
    }
    form.title = data.title;
    form.fraud_type_id = data.fraud_type_id;
    form.desensitized_summary = data.desensitized_summary;
    form.identification_points = data.identification_points;
    form.prevention_advice = data.prevention_advice;
    form.peak_periods = data.peak_periods ?? "";
    form.source_type = (data.source_type as KnowledgeSourceType) ?? "CASE";
    form.source_reference = data.source_reference ?? "";
  } catch (e) {
    errored.value = true;
    errorMsg.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

function validate(): boolean {
  errors.title = "";
  errors.fraud_type_id = "";
  errors.desensitized_summary = "";
  errors.identification_points = "";
  errors.prevention_advice = "";
  let ok = true;
  if (!form.title.trim()) {
    errors.title = "请输入标题";
    ok = false;
  }
  if (form.fraud_type_id == null) {
    errors.fraud_type_id = "请选择诈骗类型";
    ok = false;
  }
  if (!form.desensitized_summary.trim()) {
    errors.desensitized_summary = "请输入脱敏摘要";
    ok = false;
  }
  if (!form.identification_points.trim()) {
    errors.identification_points = "请输入识别要点";
    ok = false;
  }
  if (!form.prevention_advice.trim()) {
    errors.prevention_advice = "请输入防范建议";
    ok = false;
  }
  return ok;
}

function buildCreateBody(): KnowledgeCreateBody {
  return {
    title: form.title.trim(),
    fraud_type_id: form.fraud_type_id as number,
    desensitized_summary: form.desensitized_summary.trim(),
    identification_points: form.identification_points.trim(),
    prevention_advice: form.prevention_advice.trim(),
    source_type: form.source_type,
    ...(form.peak_periods.trim()
      ? { peak_periods: form.peak_periods.trim() }
      : {}),
    ...(form.source_reference.trim()
      ? { source_reference: form.source_reference.trim() }
      : {}),
  };
}

function buildUpdateBody(): KnowledgeUpdateBody {
  return {
    title: form.title.trim(),
    fraud_type_id: form.fraud_type_id as number,
    desensitized_summary: form.desensitized_summary.trim(),
    identification_points: form.identification_points.trim(),
    prevention_advice: form.prevention_advice.trim(),
    source_type: form.source_type,
    peak_periods: form.peak_periods.trim() || null,
    source_reference: form.source_reference.trim() || null,
  };
}

async function saveDraft(): Promise<void> {
  if (!validate()) {
    ElMessage.warning("请检查表单错误");
    return;
  }
  submitting.value = true;
  try {
    if (isEditMode.value) {
      await knowledgeApi.update(entryId.value, buildUpdateBody());
      ElMessage.success("草稿已更新");
      void router.push({
        name: "admin-kb-detail",
        params: { entry_id: entryId.value },
      });
    } else {
      const result = await knowledgeApi.create(buildCreateBody());
      ElMessage.success("草稿已保存");
      void router.push({
        name: "admin-kb-detail",
        params: { entry_id: result.entry_id },
      });
    }
  } catch (e) {
    if (e instanceof ApiError) ElMessage.error(e.message);
    else ElMessage.error("保存失败");
  } finally {
    submitting.value = false;
  }
}

async function saveAndSubmit(): Promise<void> {
  if (!validate()) {
    ElMessage.warning("请检查表单错误");
    return;
  }
  try {
    await ElMessageBox.confirm(
      "提交后将进入校级审核队列，期间不可编辑。确认提交？",
      "提交审核",
      { confirmButtonText: "提交", cancelButtonText: "取消" },
    );
  } catch (e) {
    if (e === "cancel" || e === "close") return;
    return;
  }
  submitting.value = true;
  try {
    let id = entryId.value;
    if (isEditMode.value) {
      await knowledgeApi.update(id, buildUpdateBody());
    } else {
      const created = await knowledgeApi.create(buildCreateBody());
      id = created.entry_id;
    }
    await knowledgeApi.submit(id);
    ElMessage.success("已保存并提交审核");
    void router.push({
      name: "admin-kb-detail",
      params: { entry_id: id },
    });
  } catch (e) {
    if (e instanceof ApiError) ElMessage.error(e.message);
    else ElMessage.error("提交失败");
  } finally {
    submitting.value = false;
  }
}

function goBack(): void {
  void router.push({ name: "admin-kb-list" });
}

onMounted(async () => {
  await Promise.all([loadFraudTypes(), loadEntry()]);
});
</script>

<template>
  <div class="admin-kb-editor">
    <AppPageHeader
      badge="UC-04"
      :title="isEditMode ? '编辑知识条目' : '新建知识条目'"
      :subtitle="isEditMode ? '修改后可继续保存草稿或直接提交审核' : '撰写新的反诈知识条目，先保存草稿后再提交审核'"
    >
      <template #actions>
        <AppButton variant="ghost" size="sm" @click="goBack">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
      </template>
    </AppPageHeader>

    <AppErrorState
      v-if="errored"
      title="加载失败"
      :hint="errorMsg || '请稍后重试'"
      retry-label="重新加载"
      @retry="loadEntry"
    />
    <template v-else>
      <AppCard v-if="loading" padding="lg">
        <AppSkeleton :rows="8" />
      </AppCard>
      <template v-else>
        <AppCard padding="lg">
          <div class="admin-kb-editor__form">
            <AppInput
              v-model="form.title"
              label="标题"
              placeholder="例：警惕假冒辅导员收取『新生材料费』"
              required
              :error="errors.title"
              :maxlength="128"
            />

            <div class="admin-kb-editor__group">
              <label class="admin-kb-editor__group-label">
                诈骗类型
                <span class="admin-kb-editor__group-required">*</span>
              </label>
              <div class="admin-kb-editor__chip-grid">
                <button
                  v-for="ft in fraudTypes"
                  :key="ft.type_id"
                  type="button"
                  class="admin-kb-editor__chip"
                  :class="{ 'admin-kb-editor__chip--active': form.fraud_type_id === ft.type_id }"
                  @click="selectFraudType(ft.type_id)"
                >
                  {{ ft.type_name }}
                </button>
              </div>
              <p v-if="errors.fraud_type_id" class="admin-kb-editor__err">
                {{ errors.fraud_type_id }}
              </p>
            </div>

            <AppInput
              v-model="form.desensitized_summary"
              label="脱敏摘要"
              type="textarea"
              :rows="4"
              placeholder="请用 1-2 段话描述案情，所有可识别学生身份的信息都需脱敏"
              required
              :error="errors.desensitized_summary"
              hint="1-1000 字；该内容将作为列表卡片摘要"
              :maxlength="1000"
            />

            <AppInput
              v-model="form.identification_points"
              label="识别要点"
              type="textarea"
              :rows="5"
              placeholder="列出识别此类骗局的关键信号，建议条目化"
              required
              :error="errors.identification_points"
              hint="1-2000 字；学生最先看到这部分"
              :maxlength="2000"
            />

            <AppInput
              v-model="form.prevention_advice"
              label="防范建议"
              type="textarea"
              :rows="5"
              placeholder="列出防范该骗局的具体步骤与注意事项"
              required
              :error="errors.prevention_advice"
              hint="1-2000 字"
              :maxlength="2000"
            />

            <AppInput
              v-model="form.peak_periods"
              label="高发时间段（可选）"
              placeholder="例：开学季 / 寒暑假前后 / 招聘季"
              hint="自然语言描述，便于学生理解"
              :maxlength="255"
            />

            <div class="admin-kb-editor__group">
              <label class="admin-kb-editor__group-label">来源类型</label>
              <div class="admin-kb-editor__source-grid">
                <button
                  v-for="s in SOURCES"
                  :key="s.value"
                  type="button"
                  class="admin-kb-editor__source"
                  :class="{ 'admin-kb-editor__source--active': form.source_type === s.value }"
                  @click="selectSource(s.value)"
                >
                  <strong>{{ s.label }}</strong>
                  <small>{{ s.desc }}</small>
                </button>
              </div>
            </div>

            <AppInput
              v-model="form.source_reference"
              label="来源引用（可选）"
              placeholder="链接、文献编号或案件号，例：CR2026-0001"
              hint="便于审核与追溯，公开后亦会显示在详情页"
              :maxlength="255"
            />
          </div>
        </AppCard>

        <div class="admin-kb-editor__footer">
          <AppButton variant="ghost" @click="goBack">取消</AppButton>
          <AppButton
            variant="ghost"
            :loading="submitting"
            :disabled="submitting"
            @click="saveDraft"
          >
            <AppIcon name="save" :size="14" />
            保存草稿
          </AppButton>
          <AppButton
            variant="primary"
            size="lg"
            :loading="submitting"
            :disabled="submitting"
            @click="saveAndSubmit"
          >
            <AppIcon name="send" :size="14" />
            保存并提交审核
          </AppButton>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.admin-kb-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-kb-editor__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-kb-editor__group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.admin-kb-editor__group-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: 0.02em;
}

.admin-kb-editor__group-required {
  color: var(--color-danger);
  margin-left: 2px;
}

.admin-kb-editor__chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.admin-kb-editor__chip {
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

.admin-kb-editor__chip:hover {
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.admin-kb-editor__chip--active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
}

.admin-kb-editor__source-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-3);
}

.admin-kb-editor__source {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: all var(--duration-base) var(--easing-out);
}

.admin-kb-editor__source strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.admin-kb-editor__source small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-kb-editor__source:hover {
  border-color: var(--color-brand-300);
}

.admin-kb-editor__source--active {
  background: var(--color-brand-50);
  border-color: var(--color-brand-500);
}

.admin-kb-editor__err {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-danger);
}

.admin-kb-editor__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  flex-wrap: wrap;
}
</style>
