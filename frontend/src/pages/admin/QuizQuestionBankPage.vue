<template>
  <div class="qbank">
    <AppPageHeader
      badge="UC-04"
      title="题库管理"
      :subtitle="`共 ${total} 道题目`"
    >
      <template #actions>
        <AppButton variant="ghost" size="md" @click="router.push({ name: 'admin-quiz-list' })">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
        <AppButton variant="primary" size="md" @click="openCreate">
          <AppIcon name="plus" :size="14" />
          新增题目
        </AppButton>
      </template>
    </AppPageHeader>

    <!-- 筛选栏 -->
    <AppCard padding="md">
      <div class="qbank__filters">
        <div class="qbank__filter-group">
          <span class="qbank__filter-label">难度</span>
          <button
            type="button"
            class="qbank__chip"
            :class="{ 'qbank__chip--active': difficultyFilter === null }"
            @click="difficultyFilter = null; applyFilters();"
          >全部</button>
          <button
            v-for="opt in DIFFICULTY_OPTIONS"
            :key="opt.value"
            type="button"
            class="qbank__chip"
            :class="{ 'qbank__chip--active': difficultyFilter === opt.value }"
            @click="difficultyFilter = opt.value as Difficulty; applyFilters();"
          >{{ opt.label }}</button>
        </div>
        <div class="qbank__filter-group">
          <span class="qbank__filter-label">状态</span>
          <button
            type="button"
            class="qbank__chip"
            :class="{ 'qbank__chip--active': activeFilter === null }"
            @click="activeFilter = null; applyFilters();"
          >全部</button>
          <button
            v-for="opt in ACTIVE_OPTIONS"
            :key="String(opt.value)"
            type="button"
            class="qbank__chip"
            :class="{ 'qbank__chip--active': activeFilter === opt.value }"
            @click="activeFilter = opt.value; applyFilters();"
          >{{ opt.label }}</button>
        </div>
        <div class="qbank__filter-group qbank__filter-group--search">
          <input
            v-model="keyword"
            class="qbank__search"
            type="search"
            placeholder="搜索题干 / 解析"
            @keyup.enter="applyFilters"
          />
          <AppButton variant="primary" size="sm" @click="applyFilters">
            <AppIcon name="search" :size="14" />
            搜索
          </AppButton>
          <AppButton variant="ghost" size="sm" @click="resetFilters">重置</AppButton>
        </div>
      </div>
    </AppCard>

    <!-- 表格 -->
    <AppCard padding="none">
      <div v-if="loading" class="qbank__loading">
        <AppIcon name="loader" :size="22" class="qbank__spin" />
        加载中…
      </div>
      <div v-else-if="items.length === 0" class="qbank__empty">暂无题目</div>
      <div v-else class="qbank__table-wrap">
        <table class="qbank__table">
          <thead>
            <tr>
              <th>题干</th>
              <th class="qbank__th-center">正确答案</th>
              <th class="qbank__th-center">难度</th>
              <th class="qbank__th-center">状态</th>
              <th class="qbank__th-center">知识库</th>
              <th class="qbank__th-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.question_id" class="qbank__row">
              <td class="qbank__content-cell" :title="row.content">{{ row.content }}</td>
              <td class="qbank__center-cell">
                <span class="qbank__answer-badge">{{ row.correct_answer }}</span>
              </td>
              <td class="qbank__center-cell">{{ DIFFICULTY_LABEL[row.difficulty] }}</td>
              <td class="qbank__center-cell">
                <AppStatusTag
                  :status="row.is_active ? 'success' : 'neutral'"
                  :text="row.is_active ? '启用' : '禁用'"
                />
              </td>
              <td class="qbank__center-cell">
                <span v-if="row.knowledge_entry_id" class="qbank__linked">已关联</span>
                <span v-else class="qbank__unlinked">—</span>
              </td>
              <td class="qbank__actions-cell">
                <AppButton variant="ghost" size="sm" @click="openEdit(row)">
                  编辑
                </AppButton>
                <AppButton v-if="row.is_active" variant="ghost" size="sm" @click="remove(row)" class="qbank__btn-danger-text">
                  禁用
                </AppButton>
                <AppButton v-else variant="ghost" size="sm" @click="enableQuestion(row)">
                  启用
                </AppButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </AppCard>

    <!-- 分页 -->
    <div v-if="total > size" class="qbank__pager">
      <AppButton variant="ghost" size="sm" :disabled="page <= 1" @click="prevPage">上一页</AppButton>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <AppButton variant="ghost" size="sm" :disabled="page >= totalPages" @click="nextPage">下一页</AppButton>
    </div>

    <!-- 新增 / 编辑对话框 -->
    <AppModal 
      v-model="dialogOpen" 
      :title="editing ? '编辑题目' : '新增题目'" 
      width="700px" 
      class="dark-red-modal"
    >
      <ElForm label-width="100px" class="dark-red-form">
        <ElFormItem label="题干" class="dark-red-form-item">
          <ElInput 
            v-model="form.content" 
            type="textarea" 
            :rows="3" 
            maxlength="500" 
            show-word-limit 
            class="dark-red-input"
          />
        </ElFormItem>
        
        <ElFormItem label="选项 A" class="dark-red-form-item">
          <ElInput v-model="form.option_a" maxlength="512" class="dark-red-input" />
        </ElFormItem>
        
        <ElFormItem label="选项 B" class="dark-red-form-item">
          <ElInput v-model="form.option_b" maxlength="512" class="dark-red-input" />
        </ElFormItem>
        
        <ElFormItem label="选项 C" class="dark-red-form-item">
          <ElInput v-model="form.option_c" maxlength="512" class="dark-red-input" />
        </ElFormItem>
        
        <ElFormItem label="选项 D" class="dark-red-form-item">
          <ElInput v-model="form.option_d" maxlength="512" class="dark-red-input" />
        </ElFormItem>
        
        <ElFormItem label="正确答案" class="dark-red-form-item">
          <ElSelect v-model="form.correct_answer" class="dark-red-select" style="width: 120px" popper-class="dark-red-popper">
            <el-option v-for="opt in ['A','B','C','D']" :key="opt" :value="opt" :label="opt" />
          </ElSelect>
        </ElFormItem>
        
        <ElFormItem label="难度" class="dark-red-form-item">
          <ElSelect v-model="form.difficulty" class="dark-red-select" style="width: 120px" popper-class="dark-red-popper">
            <el-option :value="1" label="简单" />
            <el-option :value="2" label="中等" />
            <el-option :value="3" label="困难" />
          </ElSelect>
        </ElFormItem>
        
        <ElFormItem label="解析" class="dark-red-form-item">
          <ElInput 
            v-model="form.explanation" 
            type="textarea" 
            :rows="2" 
            maxlength="2000" 
            show-word-limit 
            class="dark-red-input"
          />
        </ElFormItem>
        
        <ElFormItem label="诈骗类型" class="dark-red-form-item">
          <ElSelect
            v-model="form.fraud_type_id"
            filterable
            clearable
            placeholder="选择诈骗类型"
            class="dark-red-select"
            style="width: 260px"
            popper-class="dark-red-popper"
          >
            <el-option
              v-for="opt in fraudTypeOptions"
              :key="opt.value"
              :value="opt.value"
              :label="opt.label"
            />
          </ElSelect>
        </ElFormItem>
        
        <ElFormItem label="知识库" class="dark-red-form-item">
          <ElSelect
            v-model="form.knowledge_entry_id"
            filterable
            clearable
            :disabled="form.fraud_type_id == null"
            class="dark-red-select"
            style="width: 360px"
            popper-class="dark-red-popper"
          >
            <el-option
              v-for="kb in filteredKnowledgeOptions"
              :key="kb.entry_id"
              :value="kb.entry_id"
              :label="kb.title"
            />
          </ElSelect>
          <div v-if="form.fraud_type_id == null" class="dark-red-hint">请先选择诈骗类型</div>
        </ElFormItem>
        
        <ElFormItem v-if="editing" label="启用" class="dark-red-form-item">
          <ElSwitch
            v-model="form.is_active"
            class="dark-red-switch"
            :active-text="'启用'"
            :inactive-text="'禁用'"
            inline-prompt
            active-color="#8B0000"
            inactive-color="#c0c4cc"
          />
        </ElFormItem>
      </ElForm>

      <template #footer>
        <AppButton variant="ghost" size="md" @click="dialogOpen = false" class="dark-red-btn-cancel">取消</AppButton>
        <AppButton variant="primary" size="md" :loading="saving" @click="save" class="dark-red-btn-save">
          <AppIcon name="save" :size="14" />
          保存
        </AppButton>
      </template>
    </AppModal>

    <!-- 禁用确认弹窗 -->
    <AppModal v-model="removeOpen" title="确认禁用" width="420px" class="dark-red-modal">
      <div class="qbank__confirm">
        <div class="dark-red-confirm-icon">
          <AppIcon name="alert-triangle" :size="24" />
        </div>
        <div class="qbank__confirm-body">
          <p class="qbank__confirm-title">禁用题目后将不再随机抽取</p>
          <p class="qbank__confirm-desc" v-if="removeTarget">
            题目「{{ removeTarget.content.slice(0, 40) }}{{ removeTarget.content.length > 40 ? "…" : "" }}」将被禁用，已发起的指定测验不受影响。可以随时重新启用。
          </p>
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="removeOpen = false" class="dark-red-btn-cancel">取消</AppButton>
        <AppButton variant="danger" :loading="removing" @click="confirmRemove" class="dark-red-btn-danger">
          <AppIcon name="trash-2" :size="13" />
          确认禁用
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElSelect,
  ElSwitch,
} from "element-plus";
import { quizApi, DIFFICULTY_LABEL } from "@/api/quiz";
import { reportsApi } from "@/api/reports";
import { knowledgeApi } from "@/api/knowledge";
import type { FraudType } from "@/types/report";
import type {
  Difficulty,
  QuestionAdmin,
  QuestionCreateBody,
} from "@/types/quiz";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppModal,
  AppPageHeader,
  AppStatusTag,
} from "@/components";

const router = useRouter();

const loading = ref(false);
const items = ref<QuestionAdmin[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const keyword = ref("");
const difficultyFilter = ref<Difficulty | null>(null);
const activeFilter = ref<boolean | null>(null);

const dialogOpen = ref(false);
const editing = ref<QuestionAdmin | null>(null);
const removeOpen = ref(false);
const removeTarget = ref<QuestionAdmin | null>(null);
const removing = ref(false);
const form = reactive<{
  content: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: "A" | "B" | "C" | "D";
  explanation: string;
  difficulty: 1 | 2 | 3;
  fraud_type_id: number | null;
  knowledge_entry_id: string | null;
  is_active: boolean;
}>({
  content: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  correct_answer: "A",
  explanation: "",
  difficulty: 1,
  fraud_type_id: null,
  knowledge_entry_id: null,
  is_active: true,
});
const saving = ref(false);

const fraudTypes = ref<FraudType[]>([]);
const knowledgeOptions = ref<Array<{ entry_id: string; title: string; fraud_type_id: number }>>([]);

const filteredKnowledgeOptions = computed(() => {
  if (form.fraud_type_id == null) return [];
  return knowledgeOptions.value.filter((x) => x.fraud_type_id === form.fraud_type_id);
});

const fraudTypeOptions = computed(() =>
  fraudTypes.value
    .slice()
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((t) => ({ value: t.type_id, label: t.type_name })),
);

const DIFFICULTY_OPTIONS = [
  { value: 1, label: "简单" },
  { value: 2, label: "中等" },
  { value: 3, label: "困难" },
];

const ACTIVE_OPTIONS = [
  { value: true, label: "启用" },
  { value: false, label: "禁用" },
];

async function load(): Promise<void> {
  loading.value = true;
  try {
    const r = await quizApi.listQuestions({
      page: page.value,
      size: size.value,
      ...(keyword.value ? { keyword: keyword.value } : {}),
      ...(difficultyFilter.value ? { difficulty: difficultyFilter.value } : {}),
      ...(activeFilter.value !== null ? { is_active: activeFilter.value } : {}),
    });
    items.value = r.items;
    total.value = r.total;
  } catch {
    items.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

async function loadFraudTypes(): Promise<void> {
  try {
    fraudTypes.value = await reportsApi.listFraudTypes();
  } catch (e) {
    fraudTypes.value = [];
    ElMessage.error(e instanceof ApiError ? e.message : "加载诈骗类型失败");
  }
}

async function loadKnowledgeOptions(): Promise<void> {
  try {
    // 下拉菜单只需要“可选的已发布知识条目”，用 public 接口避免管理权限导致的空列表。
    const r = await knowledgeApi.listPublic({ page: 1, size: 100, sort: "published_at_desc" });
    knowledgeOptions.value = r.items.map((it) => ({
      entry_id: it.entry_id,
      title: it.title,
      fraud_type_id: it.fraud_type_id,
    }));
  } catch (e) {
    knowledgeOptions.value = [];
    ElMessage.error(e instanceof ApiError ? e.message : "加载知识库失败");
  }
}

function openCreate(): void {
  editing.value = null;
  Object.assign(form, {
    content: "", option_a: "", option_b: "", option_c: "", option_d: "",
    correct_answer: "A", explanation: "", difficulty: 1,
    fraud_type_id: null, knowledge_entry_id: null, is_active: true,
  });
  dialogOpen.value = true;
}

function openEdit(q: QuestionAdmin): void {
  editing.value = q;
  Object.assign(form, {
    content: q.content,
    option_a: q.option_a,
    option_b: q.option_b,
    option_c: q.option_c,
    option_d: q.option_d,
    correct_answer: q.correct_answer,
    explanation: q.explanation ?? "",
    difficulty: q.difficulty,
    fraud_type_id: q.fraud_type_id,
    knowledge_entry_id: q.knowledge_entry_id || null,
    is_active: q.is_active,
  });
  dialogOpen.value = true;
}

async function save(): Promise<void> {
  if (form.content.trim().length < 1) { ElMessage.warning("题干不能为空"); return; }
  saving.value = true;
  try {
    const body: QuestionCreateBody = {
      content: form.content, option_a: form.option_a, option_b: form.option_b,
      option_c: form.option_c, option_d: form.option_d, correct_answer: form.correct_answer,
      explanation: form.explanation || null, difficulty: form.difficulty,
      fraud_type_id: form.fraud_type_id ?? null,
      knowledge_entry_id: form.knowledge_entry_id ? Number(form.knowledge_entry_id) : null,
    };
    if (editing.value) {
      await quizApi.updateQuestion(editing.value.question_id, { ...body, is_active: form.is_active ?? true });
      ElMessage.success("已保存");
    } else {
      await quizApi.createQuestion(body);
      ElMessage.success("已新增");
    }
    dialogOpen.value = false;
    await load();
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

async function remove(q: QuestionAdmin): Promise<void> {
  removeTarget.value = q;
  removeOpen.value = true;
}

async function confirmRemove(): Promise<void> {
  if (!removeTarget.value) return;
  removing.value = true;
  try {
    await quizApi.deleteQuestion(removeTarget.value.question_id);
    ElMessage.success("已禁用");
    removeOpen.value = false;
    removeTarget.value = null;
    await load();
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "操作失败");
  } finally {
    removing.value = false;
  }
}

async function enableQuestion(q: QuestionAdmin): Promise<void> {
  try {
    await quizApi.updateQuestion(q.question_id, { is_active: true });
    ElMessage.success("已启用");
    await load();
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "操作失败");
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size.value)));

function prevPage() { if (page.value > 1) { page.value -= 1; void load(); } }
function nextPage() { if (page.value < totalPages.value) { page.value += 1; void load(); } }

function applyFilters(): void { page.value = 1; void load(); }
function resetFilters(): void {
  page.value = 1; keyword.value = "";
  difficultyFilter.value = null; activeFilter.value = null;
  void load();
}

watch(
  () => form.fraud_type_id,
  (next, prev) => {
    if (next !== prev) {
      form.knowledge_entry_id = null;
    }
  },
);

onMounted(async () => {
  await Promise.all([loadFraudTypes(), loadKnowledgeOptions()]);
  await load();
});
</script>

<style scoped>
/* ========== 主页面样式（保持不变） ========== */
.qbank {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);

  /* 覆盖 Element Plus 蓝色主色为暗红色 */
  --el-color-primary:         #9c2c3c;
  --el-color-primary-light-3: #b55c6c;
  --el-color-primary-light-5: #ce8e98;
  --el-color-primary-light-7: #e4c0c6;
  --el-color-primary-light-8: #eecfd3;
  --el-color-primary-light-9: #f7e8ea;
  --el-color-primary-dark-2:  #7d2330;
}

.qbank__filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.qbank__filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.qbank__filter-group--search {
  margin-top: var(--space-1);
}

.qbank__filter-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  min-width: 36px;
}

.qbank__chip {
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

.qbank__chip:hover {
  border-color: #c25060;
  color: #7d2330;
}

.qbank__chip--active {
  background: linear-gradient(135deg, #9c2c3c, #7d2330);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 0 0 3px rgb(156 44 60 / 20%);
}

.qbank__search {
  flex: 1;
  min-width: 200px;
  padding: 8px var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--font-size-sm);
  font-family: inherit;
  transition: border-color var(--duration-base) var(--easing-out), box-shadow var(--duration-base) var(--easing-out);
}

.qbank__search:focus {
  outline: none;
  border-color: #9c2c3c;
  box-shadow: 0 0 0 3px rgb(156 44 60 / 20%);
}

.qbank__loading,
.qbank__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  gap: var(--space-2);
}

.qbank__spin {
  animation: qbank-spin 1s linear infinite;
}

@keyframes qbank-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.qbank__table-wrap {
  overflow-x: auto;
}

.qbank__table {
  width: 100%;
  border-collapse: collapse;
}

.qbank__table th,
.qbank__table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  white-space: nowrap;
  vertical-align: middle;
}

.qbank__table thead th {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--color-bg-soft);
}

.qbank__th-center { text-align: left !important; }
.qbank__th-right { text-align: right !important; }

.qbank__row {
  transition: background var(--duration-fast) var(--easing-out);
}

.qbank__row:hover {
  background: var(--color-bg-soft);
}

.qbank__content-cell {
  color: var(--color-text-strong);
  max-width: 340px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 200px;
}

.qbank__center-cell {
  text-align: left;
}

.qbank__answer-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #9c2c3c, #7d2330);
  color: #fff;
  font-size: 12px;
  font-weight: var(--font-weight-semibold);
}

.qbank__linked {
  font-size: var(--font-size-xs);
  color: #9c2c3c;
}

.qbank__unlinked {
  color: var(--color-text-secondary);
}

.qbank__actions-cell {
  text-align: right;
  display: flex;
  justify-content: flex-end;
  gap: var(--space-1);
}

.qbank__btn-danger-text {
  color: var(--color-danger);
}

.qbank__btn-danger-text:hover:not(:disabled) {
  background: rgba(198, 40, 40, 0.08);
  color: #b71c1c;
}

.qbank__pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.qbank__confirm {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.qbank__confirm-body {
  flex: 1;
  min-width: 0;
}

.qbank__confirm-title {
  margin: 0 0 var(--space-1);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.qbank__confirm-desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.65;
}

/* ========== 弹窗暗红色主题样式（全部暗红色） ========== */

/* 弹窗整体 */
:deep(.dark-red-modal .el-modal__header) {
  border-bottom: 2px solid #8B0000;
  background: #fff;
  border-radius: 12px 12px 0 0;
  padding: 20px 24px;
}

:deep(.dark-red-modal .el-modal__title) {
  color: #8B0000;
  font-weight: 600;
  font-size: 16px;
}

:deep(.dark-red-modal .el-modal__close) {
  color: #8B0000;
}

:deep(.dark-red-modal .el-modal__close:hover) {
  color: #b71c1c;
  background: rgba(139, 0, 0, 0.1);
}

:deep(.dark-red-modal .el-modal__body) {
  background: #fff;
  padding: 24px;
}

:deep(.dark-red-modal .el-modal__footer) {
  border-top: 1px solid #f0f0f0;
  background: #fff;
  border-radius: 0 0 12px 12px;
  padding: 16px 24px;
}

/* 表单标签 */
.dark-red-form-item {
  margin-bottom: 20px;
}

.dark-red-form-item :deep(.el-form-item__label) {
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

/* 输入框 */
.dark-red-input :deep(.el-input__wrapper) {
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  box-shadow: none;
  transition: all 0.2s ease;
}

.dark-red-input :deep(.el-input__wrapper:hover) {
  border-color: #8B0000;
}

.dark-red-input :deep(.el-input__wrapper.is-focus) {
  border-color: #8B0000;
  box-shadow: 0 0 0 2px rgba(139, 0, 0, 0.1);
}

.dark-red-input :deep(.el-input__inner) {
  color: #333;
}

.dark-red-input :deep(.el-textarea__inner) {
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  color: #333;
  transition: all 0.2s ease;
}

.dark-red-input :deep(.el-textarea__inner:hover) {
  border-color: #8B0000;
}

.dark-red-input :deep(.el-textarea__inner:focus) {
  border-color: #8B0000;
  box-shadow: 0 0 0 2px rgba(139, 0, 0, 0.1);
}

.dark-red-input :deep(.el-input__count) {
  color: #999;
  background: #fafafa;
}

/* 下拉选择器 - 全部暗红色 */
.dark-red-select :deep(.el-input__wrapper) {
  background: #fff;
  border: 1px solid #8B0000;
  border-radius: 6px;
  box-shadow: none;
  transition: all 0.2s ease;
}

.dark-red-select :deep(.el-input__wrapper:hover) {
  border-color: #b71c1c;
  box-shadow: 0 0 0 1px rgba(139, 0, 0, 0.2);
}

.dark-red-select :deep(.el-input__wrapper.is-focus) {
  border-color: #8B0000;
  box-shadow: 0 0 0 2px rgba(139, 0, 0, 0.15);
}

.dark-red-select :deep(.el-input__inner) {
  color: #8B0000 !important;
  font-weight: 500;
}

.dark-red-select :deep(.el-select__caret) {
  color: #8B0000;
  font-size: 14px;
}

.dark-red-select :deep(.el-select__caret:hover) {
  color: #b71c1c;
}

/* 下拉菜单面板 - 全部暗红色 */
:deep(.dark-red-popper) {
  background: #fff;
  border: 1px solid #8B0000;
  border-radius: 6px;
  box-shadow: 0 2px 12px 0 rgba(139, 0, 0, 0.15);
}

:deep(.dark-red-popper .el-select-dropdown__item) {
  color: #8B0000;
  font-weight: 500;
  transition: all 0.2s ease;
  font-size: 14px;
}

:deep(.dark-red-popper .el-select-dropdown__item:hover) {
  background: rgba(139, 0, 0, 0.08);
  color: #b71c1c;
}

:deep(.dark-red-popper .el-select-dropdown__item.selected) {
  background: rgba(139, 0, 0, 0.12);
  color: #8B0000;
  font-weight: 600;
}

/* 下拉菜单的placeholder */
.dark-red-select :deep(.el-input__inner::placeholder) {
  color: #999;
}

/* 下拉菜单的箭头图标 */
.dark-red-select :deep(.el-select__caret) {
  color: #8B0000;
}

/* 清除按钮 */
.dark-red-select :deep(.el-input__wrapper .el-icon) {
  color: #8B0000;
}

.dark-red-select :deep(.el-input__wrapper .el-icon:hover) {
  color: #b71c1c;
}

/* 开关样式：启用=暗红，禁用=灰（两种状态明显区分） */
.dark-red-switch :deep(.el-switch__core) {
  background-color: #c0c4cc;
  border-color: #c0c4cc;
  transition: all 0.2s ease;
}

.dark-red-switch :deep(.el-switch__core .el-switch__action) {
  background: #ffffff;
}

.dark-red-switch :deep(.el-switch.is-checked .el-switch__core) {
  background-color: #8B0000;
  border-color: #8B0000;
}

.dark-red-switch :deep(.el-switch.is-checked .el-switch__core .el-switch__action) {
  background: #ffffff;
}


/* 按钮样式 */
.dark-red-btn-save {
  background: #8B0000;
  border: none;
  color: #fff;
  border-radius: 6px;
  padding: 8px 20px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.dark-red-btn-save:hover:not(:disabled) {
  background: #b71c1c;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(139, 0, 0, 0.3);
}

.dark-red-btn-cancel {
  background: #fff;
  border: 1px solid #8B0000;
  color: #8B0000;
  border-radius: 6px;
  padding: 8px 20px;
  transition: all 0.2s ease;
}

.dark-red-btn-cancel:hover:not(:disabled) {
  background: rgba(139, 0, 0, 0.05);
  border-color: #b71c1c;
  color: #b71c1c;
}

.dark-red-btn-danger {
  background: #fff;
  border: 1px solid #8B0000;
  color: #8B0000;
  border-radius: 6px;
  padding: 8px 20px;
  transition: all 0.2s ease;
}

.dark-red-btn-danger:hover:not(:disabled) {
  background: rgba(139, 0, 0, 0.08);
  border-color: #b71c1c;
  color: #b71c1c;
}

/* 禁用确认弹窗图标 */
.dark-red-confirm-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(139, 0, 0, 0.1);
  color: #8B0000;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 滚动条样式 */
:deep(.dark-red-modal .el-modal__body::-webkit-scrollbar) {
  width: 6px;
}

:deep(.dark-red-modal .el-modal__body::-webkit-scrollbar-track) {
  background: #f5f5f5;
  border-radius: 3px;
}

:deep(.dark-red-modal .el-modal__body::-webkit-scrollbar-thumb) {
  background: #8B0000;
  border-radius: 3px;
}

:deep(.dark-red-modal .el-modal__body::-webkit-scrollbar-thumb:hover) {
  background: #b71c1c;
}

/* 聚焦时的边框颜色 */
.dark-red-select :deep(.el-input__wrapper.is-focus) {
  border-color: #8B0000 !important;
  box-shadow: 0 0 0 2px rgba(139, 0, 0, 0.15) !important;
}

/* 禁用状态 */
.dark-red-select :deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f5f5;
  border-color: #d4d4d4;
}

.dark-red-select :deep(.el-input.is-disabled .el-input__inner) {
  color: #999;
}
</style>

<!-- ElSelect 下拉层通过 teleport 挂到 <body>，scoped :deep() 无法命中，必须用全局样式覆盖 -->
<style>
/* ABCD / 难度 / 诈骗类型 / 知识库 下拉面板 */
.dark-red-popper {
  --el-color-primary:         #9c2c3c !important;
  --el-color-primary-light-3: #b55c6c !important;
  --el-color-primary-light-5: #ce8e98 !important;
  --el-color-primary-light-7: #e4c0c6 !important;
  --el-color-primary-light-9: #f7e8ea !important;
  border: 1px solid #9c2c3c !important;
  box-shadow: 0 2px 12px 0 rgb(156 44 60 / 15%) !important;
}

.dark-red-popper .el-select-dropdown__item {
  color: #8B0000;
  font-weight: 500;
}

.dark-red-popper .el-select-dropdown__item:hover,
.dark-red-popper .el-select-dropdown__item.hover {
  background: rgb(156 44 60 / 8%);
  color: #9c2c3c;
}

.dark-red-popper .el-select-dropdown__item.selected,
.dark-red-popper .el-select-dropdown__item.is-selected {
  background: rgb(156 44 60 / 12%);
  color: #8B0000;
  font-weight: 600;
}

/* 滚动条 */
.dark-red-popper .el-scrollbar__thumb {
  background: rgb(156 44 60 / 40%);
}
.dark-red-popper .el-scrollbar__thumb:hover {
  background: #9c2c3c;
}

/* ============================================================
   AppModal 也通过 teleport 渲染，scoped 样式无法命中。
   .dark-red-select 的输入框样式必须在全局生效。
   ============================================================ */

/* 输入框边框 */
.dark-red-select .el-input__wrapper {
  background: #fff !important;
  border: 1px solid #8B0000 !important;
  border-radius: 6px !important;
  box-shadow: none !important;
  transition: all 0.2s ease;
}
.dark-red-select .el-input__wrapper:hover {
  border-color: #b71c1c !important;
  box-shadow: 0 0 0 1px rgb(139 0 0 / 20%) !important;
}
.dark-red-select .el-input__wrapper.is-focus {
  border-color: #8B0000 !important;
  box-shadow: 0 0 0 2px rgb(139 0 0 / 15%) !important;
}

/* 选中文字 / 箭头 / 清除图标 */
.dark-red-select .el-input__inner {
  color: #8B0000 !important;
  font-weight: 500;
}
.dark-red-select .el-select__caret {
  color: #8B0000 !important;
}
.dark-red-select .el-input__wrapper .el-icon {
  color: #8B0000 !important;
}
.dark-red-select .el-input__wrapper .el-icon:hover {
  color: #b71c1c !important;
}

/* placeholder */
.dark-red-select .el-input__inner::placeholder {
  color: #bbb;
}

/* 禁用态 */
.dark-red-select .el-input.is-disabled .el-input__wrapper {
  background-color: #f5f5f5 !important;
  border-color: #d4d4d4 !important;
  box-shadow: none !important;
}
.dark-red-select .el-input.is-disabled .el-input__inner {
  color: #999 !important;
}
</style>
