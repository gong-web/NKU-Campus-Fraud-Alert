<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElDatePicker, ElMessage } from "element-plus";
import { departmentsApi, type DepartmentOut } from "@/api/departments";
import {
  warningsApi,
  type WarningCreateBody,
  type WarningLevel,
  type WarningPushScope,
} from "@/api/warnings";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppInput,
  AppPageHeader,
} from "@/components";

const router = useRouter();

const departments = ref<DepartmentOut[]>([]);
const submitting = ref(false);

interface FormState {
  title: string;
  content: string;
  warning_level: WarningLevel;
  push_scope: WarningPushScope;
  target_dept_ids: number[];
  related_case_no: string;
  expires_at: Date | null;
}

const form = reactive<FormState>({
  title: "",
  content: "",
  warning_level: 1,
  push_scope: "FULL_SCHOOL",
  target_dept_ids: [],
  related_case_no: "",
  expires_at: null,
});

const errors = reactive<{
  title: string;
  content: string;
  target_dept_ids: string;
}>({
  title: "",
  content: "",
  target_dept_ids: "",
});

const LEVELS: ReadonlyArray<{
  value: WarningLevel;
  label: string;
  desc: string;
}> = [
  { value: 1, label: "提示", desc: "一般风险提醒" },
  { value: 2, label: "警告", desc: "高发风险，需关注" },
  { value: 3, label: "紧急", desc: "重大风险，仅校级可发" },
];

const SCOPES: ReadonlyArray<{
  value: WarningPushScope;
  label: string;
  desc: string;
}> = [
  { value: "FULL_SCHOOL", label: "全校", desc: "全体学生可见" },
  { value: "DEPARTMENT", label: "按院系", desc: "仅推送给所选院系" },
];

function selectLevel(level: WarningLevel): void {
  form.warning_level = level;
}

function selectScope(scope: WarningPushScope): void {
  form.push_scope = scope;
  if (scope === "FULL_SCHOOL") {
    form.target_dept_ids = [];
    errors.target_dept_ids = "";
  }
}

function toggleDept(deptId: number): void {
  const idx = form.target_dept_ids.indexOf(deptId);
  if (idx >= 0) {
    form.target_dept_ids.splice(idx, 1);
  } else {
    form.target_dept_ids.push(deptId);
  }
  errors.target_dept_ids = "";
}

async function loadDepartments(): Promise<void> {
  try {
    departments.value = await departmentsApi.list();
  } catch {
    departments.value = [];
  }
}

function validate(): boolean {
  errors.title = "";
  errors.content = "";
  errors.target_dept_ids = "";
  let ok = true;
  if (!form.title.trim()) {
    errors.title = "请输入标题";
    ok = false;
  }
  if (!form.content.trim()) {
    errors.content = "请输入正文";
    ok = false;
  }
  if (form.push_scope === "DEPARTMENT" && form.target_dept_ids.length === 0) {
    errors.target_dept_ids = "请选择至少 1 个目标院系";
    ok = false;
  }
  return ok;
}

async function submit(): Promise<void> {
  if (!validate()) {
    ElMessage.warning("请检查表单错误");
    return;
  }
  submitting.value = true;
  try {
    const body: WarningCreateBody = {
      title: form.title.trim(),
      content: form.content.trim(),
      warning_level: form.warning_level,
      push_scope: form.push_scope,
      ...(form.push_scope === "DEPARTMENT"
        ? { target_dept_ids: form.target_dept_ids }
        : {}),
      ...(form.related_case_no.trim()
        ? { related_case_no: form.related_case_no.trim() }
        : {}),
      ...(form.expires_at
        ? { expires_at: form.expires_at.toISOString() }
        : {}),
    };
    const result = await warningsApi.publish(body);
    ElMessage.success("预警已发布");
    void router.push({
      name: "admin-warning-detail",
      params: { warning_id: result.warning_id },
    });
  } catch (e) {
    if (e instanceof ApiError) ElMessage.error(e.message);
    else ElMessage.error("发布失败");
  } finally {
    submitting.value = false;
  }
}

function goBack(): void {
  void router.push({ name: "admin-warning-list" });
}

onMounted(loadDepartments);
</script>

<template>
  <div class="admin-warning-editor">
    <AppPageHeader badge="UC-07" title="发布预警" subtitle="发布后立即推送给学生端，请仔细核对">
      <template #actions>
        <AppButton variant="ghost" size="sm" @click="goBack">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
      </template>
    </AppPageHeader>

    <AppCard padding="lg">
      <div class="admin-warning-editor__form">
        <AppInput
          v-model="form.title"
          label="标题"
          placeholder="例：警惕假冒辅导员收取『新生材料费』"
          required
          :error="errors.title"
          :maxlength="80"
        />

        <AppInput
          v-model="form.content"
          label="正文"
          type="textarea"
          :rows="8"
          placeholder="请简述事件经过、识别要点、应对建议"
          required
          :error="errors.content"
          hint="填写正文后学生即可看到"
        />

        <div class="admin-warning-editor__group">
          <label class="admin-warning-editor__group-label">
            预警等级
            <span class="admin-warning-editor__group-required">*</span>
          </label>
          <div class="admin-warning-editor__level-grid">
            <button
              v-for="lv in LEVELS"
              :key="lv.value"
              type="button"
              class="admin-warning-editor__level"
              :class="[
                `admin-warning-editor__level--${lv.value === 3 ? 'urgent' : lv.value === 2 ? 'warning' : 'info'}`,
                { 'admin-warning-editor__level--active': form.warning_level === lv.value },
              ]"
              @click="selectLevel(lv.value)"
            >
              <strong>{{ lv.label }}级</strong>
              <small>{{ lv.desc }}</small>
            </button>
          </div>
        </div>

        <div class="admin-warning-editor__group">
          <label class="admin-warning-editor__group-label">
            推送范围
            <span class="admin-warning-editor__group-required">*</span>
          </label>
          <div class="admin-warning-editor__scope-grid">
            <button
              v-for="sc in SCOPES"
              :key="sc.value"
              type="button"
              class="admin-warning-editor__scope"
              :class="{ 'admin-warning-editor__scope--active': form.push_scope === sc.value }"
              @click="selectScope(sc.value)"
            >
              <strong>{{ sc.label }}</strong>
              <small>{{ sc.desc }}</small>
            </button>
          </div>
        </div>

        <div v-if="form.push_scope === 'DEPARTMENT'" class="admin-warning-editor__group">
          <label class="admin-warning-editor__group-label">
            目标院系
            <span class="admin-warning-editor__group-required">*</span>
          </label>
          <div class="admin-warning-editor__dept-grid">
            <button
              v-for="d in departments"
              :key="d.dept_id"
              type="button"
              class="admin-warning-editor__dept"
              :class="{ 'admin-warning-editor__dept--active': form.target_dept_ids.includes(d.dept_id) }"
              @click="toggleDept(d.dept_id)"
            >
              {{ d.dept_name }}
            </button>
          </div>
          <p
            v-if="errors.target_dept_ids"
            class="admin-warning-editor__err"
          >
            {{ errors.target_dept_ids }}
          </p>
        </div>

        <AppInput
          v-model="form.related_case_no"
          label="关联案件编号（可选）"
          placeholder="例：CR2026-0001"
          hint="若该预警与某具体上报案件相关，可在此引用"
          :maxlength="40"
        />

        <div class="admin-warning-editor__group">
          <label class="admin-warning-editor__group-label">失效时间（可选）</label>
          <ElDatePicker
            v-model="form.expires_at"
            type="datetime"
            placeholder="选择日期与时间"
            value-format="x"
          />
          <p class="admin-warning-editor__hint">
            <AppIcon name="info" :size="13" />
            到期后系统自动下线，留空表示长期生效
          </p>
        </div>
      </div>
    </AppCard>

    <div class="admin-warning-editor__footer">
      <AppButton variant="ghost" @click="goBack">取消</AppButton>
      <AppButton
        variant="primary"
        size="lg"
        :loading="submitting"
        :disabled="submitting"
        @click="submit"
      >
        <AppIcon name="send" :size="14" />
        发布预警
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.admin-warning-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-warning-editor__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-warning-editor__group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.admin-warning-editor__group-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: 0.02em;
}

.admin-warning-editor__group-required {
  color: var(--color-danger);
  margin-left: 2px;
}

.admin-warning-editor__level-grid,
.admin-warning-editor__scope-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-3);
}

.admin-warning-editor__level,
.admin-warning-editor__scope {
  position: relative;
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

.admin-warning-editor__level strong,
.admin-warning-editor__scope strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.admin-warning-editor__level small,
.admin-warning-editor__scope small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-warning-editor__level:hover,
.admin-warning-editor__scope:hover {
  border-color: var(--color-brand-300);
}

.admin-warning-editor__level--info.admin-warning-editor__level--active {
  background: rgb(25 118 210 / 8%);
  border-color: var(--color-warn-info, var(--color-info));
}

.admin-warning-editor__level--warning.admin-warning-editor__level--active {
  background: rgb(239 108 0 / 8%);
  border-color: var(--color-warn-warning, var(--color-warning));
}

.admin-warning-editor__level--urgent.admin-warning-editor__level--active {
  background: rgb(198 40 40 / 8%);
  border-color: var(--color-warn-urgent, var(--color-danger));
}

.admin-warning-editor__scope--active {
  background: var(--color-brand-50);
  border-color: var(--color-brand-500);
}

.admin-warning-editor__dept-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.admin-warning-editor__dept {
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

.admin-warning-editor__dept:hover {
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.admin-warning-editor__dept--active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
}

.admin-warning-editor__hint {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-warning-editor__err {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-danger);
}

.admin-warning-editor__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
