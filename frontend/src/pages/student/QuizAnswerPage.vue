<!-- QuizAnswerPage.vue (统一风格后) -->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { quizApi } from "@/api/quiz";
import type {
  OptionLetter,
  StartQuizOut,
  StudentQuestion,
  SubmitQuizOut,
} from "@/types/quiz";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppEmpty,
  AppIcon,
  AppModal,
  AppPageHeader,
  AppStatusTag,
} from "@/components";

const route = useRoute();
const router = useRouter();

const attemptId = computed<string>(() => String(route.params.attempt_id));

const STORAGE_PREFIX = "quiz-answer:";

function storageKey(): string {
  return `${STORAGE_PREFIX}${attemptId.value}`;
}

function persistToStorage(): void {
  try {
    const payload = {
      start: start.value,
      result: result.value,
    };
    sessionStorage.setItem(storageKey(), JSON.stringify(payload));
  } catch {
    // ignore
  }
}

function restoreFromStorage(): void {
  try {
    const raw = sessionStorage.getItem(storageKey());
    if (!raw) return;
    const parsed = JSON.parse(raw) as {
      start?: StartQuizOut | null;
      result?: SubmitQuizOut | null;
    };

    if (!start.value && parsed.start) start.value = parsed.start;
    if (!result.value && parsed.result) result.value = parsed.result;
  } catch {
    // ignore
  }
}

const start = ref<StartQuizOut | null>(
  (history.state?.start as StartQuizOut | undefined) ?? null,
);

const currentIndex = ref(0);
const answers = ref<Record<string, OptionLetter | null>>({});
const submitting = ref(false);
const result = ref<SubmitQuizOut | null>(null);

const current = computed<StudentQuestion | null>(() => {
  if (!start.value) return null;
  return start.value.questions[currentIndex.value] ?? null;
});

const progressPct = computed<number>(() => {
  if (!start.value) return 0;
  return Math.round(((currentIndex.value + 1) / start.value.questions.length) * 100);
});

const answeredCount = computed<number>(() => {
  if (!start.value) return 0;
  return start.value.questions.filter(
    (q) => answers.value[q.question_id] != null,
  ).length;
});

const allAnswered = computed<boolean>(() => {
  if (!start.value) return false;
  return start.value.questions.every(
    (q) => answers.value[q.question_id] != null,
  );
});

const OPTS: readonly OptionLetter[] = ["A", "B", "C", "D"];

const confirmOpen = ref(false);
const exitConfirmOpen = ref(false);

function optKey(q: StudentQuestion, opt: OptionLetter) {
  return q[`option_${opt.toLowerCase()}` as "option_a" | "option_b" | "option_c" | "option_d"];
}

function prev(): void {
  if (currentIndex.value > 0) currentIndex.value -= 1;
}

function next(): void {
  if (!start.value) return;
  if (currentIndex.value < start.value.questions.length - 1) currentIndex.value += 1;
}

function trySubmit(): void {
  if (!start.value) return;
  if (!allAnswered.value) {
    confirmOpen.value = true;
    return;
  }
  void doSubmit();
}

async function doSubmit(): Promise<void> {
  if (!start.value) return;
  confirmOpen.value = false;
  submitting.value = true;
  try {
    const body = {
      answers: start.value.questions.map((q) => ({
        // 雪花 ID 可能超出 JS 安全整数；这里必须传 string，后端会再转 int。
        question_id: q.question_id,
        chosen_answer: answers.value[q.question_id] ?? null,
      })),
    };
    result.value = await quizApi.submit(attemptId.value, body);
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "提交失败");
  } finally {
    submitting.value = false;
  }
}

function tryBackToList(): void {
  if (result.value || !start.value) {
    backToList();
    return;
  }
  exitConfirmOpen.value = true;
}

function confirmExit(): void {
  exitConfirmOpen.value = false;
  backToList();
}

function openKb(entryId: string | null): void {
  if (!entryId) {
    ElMessage.info("本题暂未关联知识库条目");
    return;
  }
  persistToStorage();
  void router.push({
    name: "kb-detail",
    params: { entry_id: entryId },
    query: { from: "quiz-answer", attempt_id: String(attemptId.value) },
  });
}

function backToList(): void {
  void router.push({ name: "quiz-entry" });
}

function goHistory(): void {
  void router.push({ name: "quiz-history" });
}

watch([start, result], () => {
  if (start.value || result.value) persistToStorage();
});

onMounted(() => {
  if (!start.value) restoreFromStorage();
  if (!start.value) {
    ElMessage.warning("测验数据已失效，请回到入口重新开始");
  }
});
</script>

<template>
  <div class="quiz-answer">
    <!-- 数据丢失 -->
    <AppCard v-if="!start && !result" padding="lg">
      <AppEmpty
        title="测验数据丢失"
        hint="请回到安全测验入口重新开始"
        illustration="default"
      />
      <div class="quiz-answer__empty-action">
        <AppButton variant="primary" @click="backToList">
          <AppIcon name="arrow-left" :size="14" />
          返回测验入口
        </AppButton>
      </div>
    </AppCard>

    <!-- ── 答题中 ── -->
    <template v-else-if="start && !result">
      <!-- 顶部进度头 -->
      <div class="quiz-answer__head">
        <div class="quiz-answer__head-corner" aria-hidden="true" />
        <div class="quiz-answer__head-info">
          <h2 class="quiz-answer__head-title">{{ start.title }}</h2>
          <div class="quiz-answer__head-meta">
            <span class="quiz-answer__meta-cell">
              <AppIcon name="list-checks" :size="13" />
              {{ currentIndex + 1 }} / {{ start.questions.length }} 题
            </span>
            <span class="quiz-answer__meta-cell">
              <AppIcon name="circle-check" :size="13" />
              已作答 {{ answeredCount }} 题
            </span>
            <span class="quiz-answer__meta-cell">
              <AppIcon name="shield-check" :size="13" />
              及格 {{ start.pass_score }} 分
            </span>
          </div>
        </div>
        <div class="quiz-answer__progress-wrap">
          <div class="quiz-answer__progress-track">
            <div
              class="quiz-answer__progress-fill"
              :style="{ width: progressPct + '%' }"
            />
          </div>
          <span class="quiz-answer__progress-pct">{{ progressPct }}%</span>
        </div>
        <div class="quiz-answer__head-actions">
          <AppButton variant="ghost" size="sm" @click="tryBackToList">
            <AppIcon name="arrow-left" :size="13" />
            返回列表
          </AppButton>
        </div>
      </div>

      <!-- 题目卡 -->
      <div v-if="current" class="quiz-answer__card">
        <span class="quiz-answer__card-corner" aria-hidden="true" />
        <!-- 题号 + 题干 -->
        <div class="quiz-answer__qtitle">
          <span class="quiz-answer__q-index">{{ currentIndex + 1 }}</span>
          <p class="quiz-answer__q-content">{{ current.content }}</p>
        </div>

        <!-- 选项列表 -->
        <ul class="quiz-answer__options">
          <li
            v-for="opt in OPTS"
            :key="opt"
            class="quiz-answer__option"
            :class="{
              'quiz-answer__option--selected': answers[current.question_id] === opt,
            }"
            @click="answers[current.question_id] = opt"
          >
            <span class="quiz-answer__opt-letter">{{ opt }}</span>
            <span class="quiz-answer__opt-text">{{ optKey(current, opt) }}</span>
            <AppIcon
              v-if="answers[current.question_id] === opt"
              name="circle-check"
              :size="16"
              class="quiz-answer__opt-check"
            />
          </li>
        </ul>

        <!-- 导航按钮 -->
        <div class="quiz-answer__nav">
          <AppButton
            variant="ghost"
            size="sm"
            :disabled="currentIndex === 0"
            @click="prev"
          >
            <AppIcon name="arrow-left" :size="13" />
            上一题
          </AppButton>
          <AppButton
            v-if="currentIndex < start.questions.length - 1"
            variant="primary"
            size="sm"
            @click="next"
          >
            下一题
            <AppIcon name="arrow-right" :size="13" />
          </AppButton>
          <AppButton
            v-else
            variant="primary"
            size="sm"
            :loading="submitting"
            @click="trySubmit"
          >
            <AppIcon name="send" :size="13" />
            提交答卷
          </AppButton>
        </div>
      </div>

      <!-- 题目快速导航 -->
      <div class="quiz-answer__dot-nav">
        <p class="quiz-answer__dot-label">题目导航</p>
        <div class="quiz-answer__dots">
          <button
            v-for="(q, idx) in start.questions"
            :key="q.question_id"
            class="quiz-answer__dot"
            :class="{
              'quiz-answer__dot--current': currentIndex === idx,
              'quiz-answer__dot--answered': answers[q.question_id] != null,
            }"
            type="button"
            @click="currentIndex = idx"
          >
            {{ idx + 1 }}
          </button>
        </div>
      </div>
    </template>

    <!-- ── 提交结果 ── -->
    <template v-else-if="result">
      <AppPageHeader
        badge="测验结果"
        :title="result.is_pass ? '🎉 恭喜通过！' : '未通过，继续加油'"
        :subtitle="`共 ${result.total_count} 题，答对 ${result.correct_count} 题`"
      />

      <!-- 成绩卡 -->
      <div class="quiz-answer__score-card" :class="{ 'quiz-answer__score-card--pass': result.is_pass }">
        <span class="quiz-answer__card-corner" aria-hidden="true" />
        <div class="quiz-answer__score-grid">
          <div class="quiz-answer__score-main">
            <span class="quiz-answer__score-num">{{ result.score }}</span>
            <span class="quiz-answer__score-unit">分</span>
          </div>
          <div class="quiz-answer__score-stats">
            <div class="quiz-answer__score-stat">
              <span class="quiz-answer__score-stat-val">{{ result.correct_count }}</span>
              <span class="quiz-answer__score-stat-key">答对</span>
            </div>
            <div class="quiz-answer__score-divider" />
            <div class="quiz-answer__score-stat">
              <span class="quiz-answer__score-stat-val">{{ result.total_count - result.correct_count }}</span>
              <span class="quiz-answer__score-stat-key">答错</span>
            </div>
            <div class="quiz-answer__score-divider" />
            <div class="quiz-answer__score-stat">
              <span class="quiz-answer__score-stat-val">{{ result.pass_score }}</span>
              <span class="quiz-answer__score-stat-key">及格分</span>
            </div>
          </div>
          <div class="quiz-answer__score-actions">
            <AppStatusTag
              :status="result.is_pass ? 'success' : 'danger'"
              :text="result.is_pass ? '已通过' : '未通过'"
            />
            <AppButton variant="ghost" size="sm" @click="backToList">
              <AppIcon name="arrow-left" :size="13" />
              返回测验入口
            </AppButton>
            <AppButton variant="primary" size="sm" @click="goHistory">
              <AppIcon name="list-checks" :size="13" />
              返回列表
            </AppButton>
          </div>
        </div>
      </div>

      <!-- 逐题解析 -->
      <ul class="quiz-answer__result-list">
        <li
          v-for="(r, idx) in result.results"
          :key="r.question_id"
          class="quiz-answer__result-item"
          :class="{ 'quiz-answer__result-item--wrong': !r.is_correct }"
        >
          <span class="quiz-answer__item-corner" aria-hidden="true" />

          <header class="quiz-answer__result-head">
            <div class="quiz-answer__result-title">
              <span class="quiz-answer__q-index--small">{{ idx + 1 }}</span>
              <h3>{{ r.content }}</h3>
            </div>
            <AppStatusTag
              :status="r.is_correct ? 'success' : 'danger'"
              :text="r.is_correct ? '答对' : '答错'"
            />
          </header>

          <ul class="quiz-answer__result-opts">
            <li
              v-for="opt in OPTS"
              :key="opt"
              class="quiz-answer__result-opt"
              :class="{
                'quiz-answer__result-opt--correct': r.correct_answer === opt,
                'quiz-answer__result-opt--chosen-wrong':
                  r.chosen_answer === opt && r.chosen_answer !== r.correct_answer,
              }"
            >
              <span class="quiz-answer__opt-letter">{{ opt }}</span>
              <span class="quiz-answer__opt-text">
                {{ r[`option_${opt.toLowerCase()}` as 'option_a' | 'option_b' | 'option_c' | 'option_d'] }}
              </span>
              <AppIcon
                v-if="r.correct_answer === opt"
                name="circle-check"
                :size="14"
                class="quiz-answer__icon-correct"
              />
              <AppIcon
                v-else-if="r.chosen_answer === opt && r.chosen_answer !== r.correct_answer"
                name="circle-x"
                :size="14"
                class="quiz-answer__icon-wrong"
              />
            </li>
          </ul>

          <div v-if="r.explanation" class="quiz-answer__explain">
            <AppIcon name="info" :size="14" />
            <div>
              <strong>解析</strong>
              <p>{{ r.explanation }}</p>
            </div>
          </div>

          <footer v-if="!r.is_correct" class="quiz-answer__result-footer">
            <AppButton
              v-if="r.knowledge_entry_id"
              variant="primary"
              size="sm"
              @click="openKb(r.knowledge_entry_id)"
            >
              <AppIcon name="book-open" :size="13" />
              前往知识库学习
              <AppIcon name="arrow-right" :size="13" />
            </AppButton>
            <span v-else class="quiz-answer__no-kb">
              <AppIcon name="info" :size="12" />
              本题暂未关联知识库
            </span>
          </footer>
        </li>
      </ul>
    </template>

    <!-- 提交确认 -->
    <AppModal
      v-model="confirmOpen"
      title="确认提交"
      width="440px"
    >
      <div class="quiz-answer__confirm">
        <div class="quiz-answer__confirm-icon quiz-answer__confirm-icon--warn">
          <AppIcon name="alert-triangle" :size="24" />
        </div>
        <div class="quiz-answer__confirm-body">
          <p class="quiz-answer__confirm-title">仍有题目未作答</p>
          <p class="quiz-answer__confirm-desc" v-if="start">
            共 {{ start.questions.length }} 题，你已作答
            <strong>{{ answeredCount }}</strong> 题，剩余
            <strong>{{ start.questions.length - answeredCount }}</strong>
            题未作答。未答题目将记为答错，是否继续提交？
          </p>
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="confirmOpen = false">
          继续作答
        </AppButton>
        <AppButton variant="primary" :loading="submitting" @click="doSubmit">
          <AppIcon name="send" :size="13" />
          确认提交
        </AppButton>
      </template>
    </AppModal>

    <!-- 退出确认 -->
    <AppModal
      v-model="exitConfirmOpen"
      title="确认退出作答"
      width="420px"
    >
      <div class="quiz-answer__confirm">
        <div class="quiz-answer__confirm-icon quiz-answer__confirm-icon--danger">
          <AppIcon name="alert-triangle" :size="24" />
        </div>
        <div class="quiz-answer__confirm-body">
          <p class="quiz-answer__confirm-title">作答进度将不保留</p>
          <p class="quiz-answer__confirm-desc">
            返回列表后，本次作答记录会保留为「进行中」状态，但已选答案不会保存到本地。是否仍要返回？
          </p>
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="exitConfirmOpen = false">
          继续作答
        </AppButton>
        <AppButton variant="danger" @click="confirmExit">
          <AppIcon name="arrow-left" :size="13" />
          确认返回
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.quiz-answer {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 820px;
  margin: 0 auto;
  width: 100%;
}

/* ── 空态 ── */
.quiz-answer__empty-action {
  display: flex;
  justify-content: center;
  margin-top: var(--space-3);
}

/* ── 确认弹窗 ── */
.quiz-answer__confirm {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.quiz-answer__confirm-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.quiz-answer__confirm-icon--warn {
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
}

.quiz-answer__confirm-icon--danger {
  background: rgb(198 40 40 / 12%);
  color: var(--color-danger);
}

.quiz-answer__confirm-body {
  flex: 1;
  min-width: 0;
}

.quiz-answer__confirm-title {
  margin: 0 0 var(--space-1);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.quiz-answer__confirm-desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.65;
}

.quiz-answer__confirm-desc strong {
  color: var(--color-brand-700);
  font-weight: var(--font-weight-semibold);
}

/* ── 进度头（统一卡片样式） ── */
.quiz-answer__head {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  overflow: hidden;
  flex-wrap: wrap;
}

.quiz-answer__head-corner {
  position: absolute;
  top: 0;
  left: 0;
  width: 16px;
  height: 16px;
  border-top: 2px solid var(--color-gold-400);
  border-left: 2px solid var(--color-gold-400);
  border-top-left-radius: var(--radius-lg);
  pointer-events: none;
}

.quiz-answer__head-title {
  margin: 0 0 var(--space-1);
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
}

.quiz-answer__head-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.quiz-answer__meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.quiz-answer__progress-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 160px;
}

.quiz-answer__progress-track {
  flex: 1;
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--color-border-soft);
  overflow: hidden;
}

.quiz-answer__progress-fill {
  height: 100%;
  border-radius: var(--radius-pill);
  background: var(--gradient-brand);
  transition: width 0.3s var(--easing-out);
}

.quiz-answer__progress-pct {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-brand-600);
  min-width: 32px;
  text-align: right;
}

.quiz-answer__head-actions {
  display: flex;
  align-items: center;
  margin-left: auto;
}

/* ── 统一卡片样式 ── */
.quiz-answer__card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  transition:
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
  overflow: hidden;
}

.quiz-answer__card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-mid);
  border-color: var(--color-brand-300);
}

.quiz-answer__card-corner {
  position: absolute;
  top: 0;
  left: 0;
  width: 16px;
  height: 16px;
  border-top: 2px solid var(--color-gold-400);
  border-left: 2px solid var(--color-gold-400);
  border-top-left-radius: var(--radius-lg);
  pointer-events: none;
}

/* ── 题目区域 ── */
.quiz-answer__qtitle {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.quiz-answer__q-index {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  font-family: var(--font-family-mono);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.quiz-answer__q-index--small {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  font-size: 11px;
  font-weight: var(--font-weight-bold);
  font-family: var(--font-family-mono);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.quiz-answer__q-content {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.55;
  padding-top: 4px;
}

/* ── 选项 ── */
.quiz-answer__options {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quiz-answer__option {
  display: grid;
  grid-template-columns: 28px 1fr 20px;
  gap: var(--space-2);
  align-items: center;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-soft);
  font-size: var(--font-size-sm);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color var(--duration-base) var(--easing-out),
    background var(--duration-base) var(--easing-out),
    transform var(--duration-base) var(--easing-out);
  user-select: none;
}

.quiz-answer__option:hover {
  border-color: var(--color-brand-300);
  background: var(--color-brand-50);
  transform: translateX(2px);
}

.quiz-answer__option--selected {
  border-color: var(--color-brand-500);
  background: rgb(var(--color-brand-rgb, 134 26 45) / 6%);
  color: var(--color-text-strong);
}

.quiz-answer__option--selected .quiz-answer__opt-letter {
  background: var(--color-brand-600);
  color: #fff;
  border-color: transparent;
}

.quiz-answer__opt-letter {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: var(--font-weight-bold);
  font-family: var(--font-family-mono);
  color: var(--color-text-secondary);
  transition: background var(--duration-base), color var(--duration-base);
}

.quiz-answer__opt-text {
  min-width: 0;
  line-height: 1.5;
}

.quiz-answer__opt-check {
  color: var(--color-brand-500);
  flex-shrink: 0;
}

/* ── 导航 ── */
.quiz-answer__nav {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px dashed var(--color-border);
}

/* ── 题目点导航（统一卡片样式） ── */
.quiz-answer__dot-nav {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  overflow: hidden;
}

.quiz-answer__dot-label {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.quiz-answer__dots {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.quiz-answer__dot {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg-soft);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-family: var(--font-family-mono);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    background var(--duration-base),
    border-color var(--duration-base),
    color var(--duration-base);
}

.quiz-answer__dot--answered {
  background: var(--color-brand-50);
  border-color: var(--color-brand-300);
  color: var(--color-brand-700);
}

.quiz-answer__dot--current {
  background: var(--gradient-brand);
  border-color: transparent;
  color: #fff;
  font-weight: var(--font-weight-bold);
}

/* ── 成绩卡（统一卡片样式） ── */
.quiz-answer__score-card {
  position: relative;
  padding: var(--space-5);
  background: var(--gradient-brand);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-mid);
  overflow: hidden;
  color: #fff;
}

.quiz-answer__score-card--pass {
  background: var(--gradient-brand);
}

.quiz-answer__score-card .quiz-answer__card-corner {
  border-color: rgba(255, 255, 255, 0.4);
}

.quiz-answer__score-grid {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.quiz-answer__score-main {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.quiz-answer__score-num {
  font-family: var(--font-family-serif);
  font-size: 56px;
  font-weight: var(--font-weight-bold);
  line-height: 1;
}

.quiz-answer__score-unit {
  font-size: var(--font-size-lg);
  color: rgb(255 255 255 / 70%);
  font-weight: var(--font-weight-medium);
}

.quiz-answer__score-stats {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex: 1;
}

.quiz-answer__score-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.quiz-answer__score-stat-val {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: rgb(255 255 255 / 95%);
}

.quiz-answer__score-stat-key {
  font-size: var(--font-size-xs);
  color: rgb(255 255 255 / 65%);
}

.quiz-answer__score-divider {
  width: 1px;
  height: 32px;
  background: rgb(255 255 255 / 20%);
}

.quiz-answer__score-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
}

/* ── 结果列表 ── */
.quiz-answer__result-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.quiz-answer__result-item {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  transition:
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
  overflow: hidden;
}

.quiz-answer__result-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-mid);
}

.quiz-answer__result-item--wrong {
  border-color: rgb(198 40 40 / 28%);
}

.quiz-answer__item-corner {
  position: absolute;
  top: 0;
  left: 0;
  width: 16px;
  height: 16px;
  border-top: 2px solid var(--color-gold-400);
  border-left: 2px solid var(--color-gold-400);
  border-top-left-radius: var(--radius-lg);
  pointer-events: none;
}

.quiz-answer__result-item--wrong .quiz-answer__item-corner {
  border-color: var(--color-danger);
}

.quiz-answer__result-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
}

.quiz-answer__result-title {
  display: flex;
  gap: var(--space-2);
  align-items: flex-start;
  min-width: 0;
}

.quiz-answer__result-title h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.45;
}

/* ── 结果选项 ── */
.quiz-answer__result-opts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.quiz-answer__result-opt {
  display: grid;
  grid-template-columns: 26px 1fr 16px;
  gap: var(--space-2);
  align-items: center;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: var(--color-bg-soft);
  font-size: var(--font-size-sm);
  color: var(--color-text);
}

.quiz-answer__result-opt--correct {
  background: rgb(46 125 50 / 8%);
  border-color: rgb(46 125 50 / 28%);
  color: var(--color-success);
  font-weight: var(--font-weight-semibold);
}

.quiz-answer__result-opt--correct .quiz-answer__opt-letter {
  background: var(--color-success);
  color: #fff;
  border-color: transparent;
}

.quiz-answer__result-opt--chosen-wrong {
  background: rgb(198 40 40 / 8%);
  border-color: rgb(198 40 40 / 28%);
  color: var(--color-danger);
  text-decoration: line-through;
}

.quiz-answer__result-opt--chosen-wrong .quiz-answer__opt-letter {
  background: var(--color-danger);
  color: #fff;
  border-color: transparent;
  text-decoration: none;
}

.quiz-answer__icon-correct { color: var(--color-success); }
.quiz-answer__icon-wrong   { color: var(--color-danger); }

/* ── 解析 ── */
.quiz-answer__explain {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(230 179 73 / 10%);
  border: 1px dashed rgb(160 120 35 / 40%);
  align-items: flex-start;
}

.quiz-answer__explain svg {
  color: var(--color-gold-500);
  flex-shrink: 0;
  margin-top: 2px;
}

.quiz-answer__explain strong {
  display: block;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gold-700);
  letter-spacing: 0.04em;
  margin-bottom: 2px;
}

.quiz-answer__explain p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text);
  line-height: 1.65;
}

/* ── 结果 footer ── */
.quiz-answer__result-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-top: var(--space-2);
  border-top: 1px dashed var(--color-border);
}

.quiz-answer__no-kb {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}
</style>