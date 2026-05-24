<template>
  <div class="wizard">
    <AppPageHeader
      badge="UC-05"
      title="发起指定测验"
      subtitle="配置基本信息、参与范围与题目，完成后一键发布"
    >
      <template #actions>
        <AppButton variant="ghost" size="md" @click="router.push({ name: 'admin-quiz-list' })">
          返回列表
        </AppButton>
      </template>
    </AppPageHeader>

    <AppCard padding="md">
      <ElSteps :active="step" finish-status="success" class="wizard__steps">
        <ElStep title="基本信息" />
        <ElStep title="参与范围" />
        <ElStep title="选择题目" />
        <ElStep title="确认发布" />
      </ElSteps>
    </AppCard>

    <AppCard padding="md">
      <!-- Step 1 -->
      <ElForm v-if="step === 0" label-width="96px" class="wizard__form">
        <ElFormItem label="标题">
          <ElInput v-model="form.title" maxlength="128" show-word-limit />
        </ElFormItem>
        <ElFormItem label="及格分">
          <ElInputNumber v-model="form.pass_score" :min="0" :max="100" />
        </ElFormItem>
        <ElFormItem label="截止时间">
          <ElDatePicker 
            v-model="form.deadline_at" 
            type="datetime" 
            value-format="YYYY-MM-DDTHH:mm:ss" 
            placeholder="选择截止时间" 
          />
        </ElFormItem>
      </ElForm>

      <!-- Step 2 -->
      <ElForm v-else-if="step === 1" label-width="96px" class="wizard__form">
        <ElFormItem label="参与范围">
          <ElRadioGroup v-model="form.scope_type">
            <template v-if="isDeptReviewer">
              <ElRadio value="DEPT">本学院</ElRadio>
              <ElRadio value="USERS">按学生</ElRadio>
            </template>
            <template v-else>
              <ElRadio value="ALL">全校</ElRadio>
              <ElRadio value="DEPT">按院系</ElRadio>
              <ElRadio value="USERS">按学生</ElRadio>
            </template>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem v-if="isDeptReviewer && form.scope_type === 'DEPT'" label="学院">
          <ElInput :model-value="myDeptId ? String(myDeptId) : ''" disabled />
        </ElFormItem>
        <ElFormItem v-else-if="form.scope_type === 'DEPT'" label="院系">
          <ElSelect
            v-model="form.dept_ids"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="选择院系（可多选）"
            style="width: 100%"
          >
            <ElOption
              v-for="d in departments"
              :key="d.dept_id"
              :label="d.dept_name"
              :value="d.dept_id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem v-if="form.scope_type === 'USERS'" label="学生 ID">
          <ElInput 
            v-model="userIdsText" 
            placeholder="逗号或空格分隔的 user_id" 
            @blur="syncUserIds" 
          />
        </ElFormItem>
      </ElForm>

      <!-- Step 3 -->
      <div v-else-if="step === 2" class="wizard__qsel">
        <div class="wizard__qsel-head">
          <input
            v-model="keyword"
            class="wizard__search"
            type="search"
            placeholder="搜索题干"
            @keyup.enter="handleSearch"
          />
          <AppButton variant="primary" size="sm" @click="handleSearch">
            <AppIcon name="search" :size="14" />
            搜索
          </AppButton>
          <span class="wizard__qsel-count">已选 <strong>{{ form.question_ids.length }}</strong> 题</span>
        </div>
        <ElTable :data="questions" v-loading="loadingQs" class="wizard__table">
          <ElTableColumn label="选择" width="56" align="center">
            <template #default="{ row }">
              <ElCheckbox 
                :model-value="isSelected(row)" 
                @change="(val: boolean) => toggleQuestion(row, val)"
              />
            </template>
          </ElTableColumn>
          <ElTableColumn label="题干" prop="content" min-width="320" show-overflow-tooltip />
          <ElTableColumn label="难度" width="90" align="center">
            <template #default="{ row }">
              <ElTag :type="getDifficultyType(row.difficulty)" size="small">
                {{ DIFFICULTY_LABEL[row.difficulty] }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="答案" prop="correct_answer" width="80" align="center" />
        </ElTable>
        <div class="wizard__pagination">
          <ElPagination
            background
            layout="prev, pager, next, total"
            :total="total"
            :page-size="size"
            :current-page="page"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- Step 4 -->
      <div v-else-if="step === 3" class="wizard__review">
        <div class="wizard__review-row">
          <span class="wizard__review-key">标题</span>
          <span class="wizard__review-val">{{ form.title }}</span>
        </div>
        <div class="wizard__review-row">
          <span class="wizard__review-key">及格分</span>
          <span class="wizard__review-val">{{ form.pass_score }}</span>
        </div>
        <div class="wizard__review-row">
          <span class="wizard__review-key">截止时间</span>
          <span class="wizard__review-val">{{ formatDate(form.deadline_at) }}</span>
        </div>
        <div class="wizard__review-row">
          <span class="wizard__review-key">参与范围</span>
          <span class="wizard__review-val">
            <ElTag size="small">{{ getScopeLabel(form.scope_type) }}</ElTag>
            <span v-if="form.scope_type === 'DEPT' && form.dept_ids.length">
               · 院系 {{ form.dept_ids.join(", ") }}
            </span>
            <span v-if="form.scope_type === 'USERS' && form.user_ids.length">
               · 学生 {{ form.user_ids.join(", ") }}
            </span>
          </span>
        </div>
        <div class="wizard__review-row">
          <span class="wizard__review-key">题目数</span>
          <span class="wizard__review-val wizard__review-val--accent">{{ form.question_ids.length }}</span>
        </div>
      </div>

      <ElDivider />
      <div class="wizard__nav">
        <AppButton variant="ghost" size="md" :disabled="step === 0" @click="prevStep">
          上一步
        </AppButton>
        <AppButton v-if="step < 3" variant="primary" size="md" class="wizard__btn-primary" @click="nextStep">
          下一步
        </AppButton>
        <AppButton v-else variant="primary" size="md" class="wizard__btn-primary" :loading="saving" @click="submit">
          确认发起
        </AppButton>
      </div>
    </AppCard>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed, watchEffect } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import {
  ElCheckbox,
  ElDatePicker,
  ElDivider,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElPagination,
  ElRadio,
  ElRadioGroup,
  ElSteps,
  ElStep,
  ElTable,
  ElTableColumn,
  ElTag,
} from "element-plus";
import { quizApi, DIFFICULTY_LABEL } from "@/api/quiz";
import { departmentsApi, type DepartmentOut } from "@/api/departments";
import type {
  AssignedQuizCreateBody,
  QuestionAdmin,
  ScopeType,
} from "@/types/quiz";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppPageHeader,
} from "@/components";

const router = useRouter();
const auth = useAuthStore();

const isDeptReviewer = computed(() => auth.me?.role_code === "REVIEWER" && auth.me?.role_level === 1);
const myDeptId = computed(() => auth.me?.department_id ?? null);

const step = ref(0);
const saving = ref(false);

const form = reactive<{
  title: string;
  pass_score: number;
  deadline_at: string;
  scope_type: ScopeType;
  dept_ids: number[];
  user_ids: number[];
  question_ids: string[];
}>({
  title: "",
  pass_score: 60,
  deadline_at: "",
  scope_type: "DEPT",
  dept_ids: [],
  user_ids: [],
  question_ids: [],
});

// Step 2: 选题目
const questions = ref<QuestionAdmin[]>([]);

// Step 2: 院系字典（按院系范围时多选）
const departments = ref<DepartmentOut[]>([]);

async function loadDepartments(): Promise<void> {
  try {
    departments.value = await departmentsApi.list();
  } catch (error) {
    ElMessage.error("加载院系列表失败");
    console.error(error);
  }
}
const total = ref(0);
const page = ref(1);
const size = ref(10);
const keyword = ref("");
const loadingQs = ref(false);

// 辅助函数：获取题目ID（始终用 string，避免 JS 大整数精度问题）
const getQuestionId = (q: QuestionAdmin): string => {
  return String(q.question_id);
};

// 检查题目是否被选中
const isSelected = (q: QuestionAdmin): boolean => {
  const id = getQuestionId(q);
  return form.question_ids.includes(id);
};

// 切换题目选中状态
function toggleQuestion(q: QuestionAdmin, picked: boolean): void {
  const id = getQuestionId(q);

  if (picked) {
    if (!form.question_ids.includes(id)) {
      form.question_ids.push(id);
    }
  } else {
    const index = form.question_ids.indexOf(id);
    if (index > -1) {
      form.question_ids.splice(index, 1);
    }
  }
}

async function loadQuestions(): Promise<void> {
  loadingQs.value = true;
  try {
    const params = {
      page: page.value,
      size: size.value,
      is_active: true,
      ...(keyword.value ? { keyword: keyword.value } : {}),
    };
    const r = await quizApi.listQuestions(params);
    questions.value = r.items;
    total.value = r.total;
  } catch (error) {
    ElMessage.error("加载题目失败");
    console.error(error);
  } finally {
    loadingQs.value = false;
  }
}

function handleSearch(): void {
  page.value = 1;
  loadQuestions();
}

function handlePageChange(newPage: number): void {
  page.value = newPage;
  loadQuestions();
}

// 获取难度对应的标签类型
function getDifficultyType(difficulty: number): "success" | "warning" | "info" | "danger" {
  const types: Record<number, "success" | "warning" | "info" | "danger"> = {
    1: "success", // 简单
    2: "warning", // 中等
    3: "danger",  // 困难
  };
  return types[difficulty] || "info";
}

// 获取范围标签文本
function getScopeLabel(scope: ScopeType): string {
  const labels: Record<ScopeType, string> = {
    'ALL': '全校',
    'DEPT': '按院系',
    'USERS': '按学生'
  };
  return labels[scope];
}

// 格式化日期
function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
}

function nextStep(): void {
  if (step.value === 0) {
    if (form.title.length < 2) { 
      ElMessage.warning("标题不能为空"); 
      return; 
    }
    if (!form.deadline_at) { 
      ElMessage.warning("请选择截止时间"); 
      return; 
    }
    if (new Date(form.deadline_at).getTime() <= Date.now()) { 
      ElMessage.warning("截止时间必须在未来"); 
      return; 
    }
  } else if (step.value === 1) {
    if (form.scope_type === "DEPT" && form.dept_ids.length === 0) { 
      ElMessage.warning("请填写至少一个院系 ID"); 
      return; 
    }
    if (form.scope_type === "USERS" && form.user_ids.length === 0) { 
      ElMessage.warning("请填写至少一个学生 user_id"); 
      return; 
    }
  } else if (step.value === 2) {
    if (form.question_ids.length < 10) {
      ElMessage.warning("请至少选择 10 道题");
      return;
    }
  }
  step.value += 1;
  
  // 进入第三步时加载题目
  if (step.value === 2 && questions.value.length === 0) {
    loadQuestions();
  }
}

function prevStep(): void {
  if (step.value > 0) step.value -= 1;
}

async function submit(): Promise<void> {
  saving.value = true;
  try {
    const body: AssignedQuizCreateBody = {
      title: form.title,
      pass_score: form.pass_score,
      deadline_at: new Date(form.deadline_at).toISOString(),
      scope_type: form.scope_type,
      question_ids: form.question_ids,
      dept_ids: form.scope_type === "DEPT" ? form.dept_ids : null,
      user_ids: form.scope_type === "USERS" ? form.user_ids : null,
    };
    const out = await quizApi.createAssigned(body);
    ElMessage.success("测验已发起");
    await router.push({ name: "admin-quiz-report", params: { quiz_id: out.quiz_id } });
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "发起失败");
  } finally {
    saving.value = false;
  }
}

const userIdsText = ref("");

function syncUserIds(): void {
  form.user_ids = userIdsText.value
    .split(/[,，\s]+/)
    .map((s) => Number(s.trim()))
    .filter((n) => Number.isFinite(n) && n > 0);
}

watchEffect(() => {
  if (!isDeptReviewer.value) return;
  if (!myDeptId.value) return;
  if (form.scope_type === "USERS") return;
  form.scope_type = "DEPT";
  form.dept_ids = [myDeptId.value];
  form.user_ids = [];
});

onMounted(() => {
  void auth.fetchMe();
  loadDepartments();
  // 初始化时不需要加载题目，等进入第三步再加载
});
</script>

	<style scoped>
	.wizard {
	  display: flex;
	  flex-direction: column;
	  gap: var(--space-4);

	  /* 将 Element Plus 全局蓝色主色覆盖为暗红色 */
	  --el-color-primary:         #9c2c3c;
	  --el-color-primary-light-3: #b55c6c;
	  --el-color-primary-light-5: #ce8e98;
	  --el-color-primary-light-7: #e4c0c6;
	  --el-color-primary-light-8: #eecfd3;
	  --el-color-primary-light-9: #f7e8ea;
	  --el-color-primary-dark-2:  #7d2330;
	}

	.wizard__steps {
	  margin-bottom: var(--space-2);
	}

	.wizard__form {
	  padding: var(--space-2) 0;
	}

	.wizard__qsel {
	  display: flex;
	  flex-direction: column;
	  gap: var(--space-3);
	}

	.wizard__qsel-head {
	  display: flex;
	  gap: var(--space-2);
	  align-items: center;
	  flex-wrap: wrap;
	}

	.wizard__search {
	  width: 260px;
	  padding: 8px var(--space-3);
	  border-radius: var(--radius-md);
	  border: 1px solid var(--color-border);
	  background: var(--color-surface);
	  color: var(--color-text);
	  font-size: var(--font-size-sm);
	  font-family: inherit;
	  transition:
	    border-color var(--duration-base) var(--easing-out),
	    box-shadow var(--duration-base) var(--easing-out);
	}

	.wizard__search:focus {
	  outline: none;
	  border-color: #9c2c3c;
	  box-shadow: 0 0 0 3px rgb(156 44 60 / 20%);
	}

	.wizard__qsel-count {
	  margin-left: auto;
	  font-size: var(--font-size-xs);
	  color: var(--color-text-secondary);
	}

	.wizard__qsel-count strong {
	  color: var(--color-brand-700);
	  font-weight: var(--font-weight-semibold);
	}

	.wizard__pagination {
	  display: flex;
	  justify-content: flex-end;
	  margin-top: var(--space-4);
	}

	.wizard__review {
	  display: flex;
	  flex-direction: column;
	  gap: var(--space-3);
	  padding: var(--space-2) 0;
	}

	.wizard__review-row {
	  display: flex;
	  align-items: center;
	  gap: var(--space-4);
	  padding: var(--space-2) 0;
	  border-bottom: 1px solid var(--color-border);
	  font-size: var(--font-size-sm);
	}

	.wizard__review-key {
	  width: 96px;
	  flex-shrink: 0;
	  font-size: 11px;
	  color: var(--color-text-secondary);
	  font-weight: var(--font-weight-semibold);
	  letter-spacing: 0.08em;
	  text-transform: uppercase;
	}

	.wizard__review-val {
	  color: var(--color-text);
	  display: flex;
	  align-items: center;
	  gap: var(--space-2);
	  flex-wrap: wrap;
	  flex: 1;
	}

	.wizard__review-val--accent {
	  color: var(--color-brand-700);
	  font-size: var(--font-size-lg);
	  font-weight: var(--font-weight-bold);
	}

	.wizard__nav {
	  display: flex;
	  justify-content: flex-end;
	  gap: var(--space-2);
	}

	.wizard__btn-primary {
	  border-color: var(--color-brand-700);
	  box-shadow: 0 0 0 1px rgb(156 44 60 / 22%);
	}

	.wizard__btn-primary:hover:not(:disabled) {
	  box-shadow:
	    0 0 0 1px rgb(156 44 60 / 32%),
	    0 0 0 3px rgb(134 38 51 / 14%);
	}

	@media (max-width: 768px) {
	  .wizard__search {
	    width: 100%;
	  }

	  .wizard__qsel-count {
	    margin-left: 0;
	    width: 100%;
	  }

	  .wizard__review-row {
	    flex-direction: column;
	    align-items: flex-start;
	    gap: var(--space-1);
	  }

	  .wizard__review-key {
	    width: auto;
	  }
	}
	</style>

<!-- 日历弹出层通过 teleport 挂载到 <body>，无法继承 scoped 变量，需单独全局覆盖 -->
<style>
.el-picker-panel {
  --el-color-primary:         #9c2c3c;
  --el-color-primary-light-3: #b55c6c;
  --el-color-primary-light-5: #ce8e98;
  --el-color-primary-light-7: #e4c0c6;
  --el-color-primary-light-9: #f7e8ea;
  --el-color-primary-dark-2:  #7d2330;
  --el-datepicker-active-color: #9c2c3c;
  --el-datepicker-border-color: #9c2c3c;
  --el-datepicker-text-color: var(--el-text-color-regular);
  --el-datepicker-off-text-color: var(--el-text-color-placeholder);
}
</style>