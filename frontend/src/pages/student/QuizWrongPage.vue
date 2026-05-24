<!-- QuizWrongPage.vue (统一风格后) -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { quizApi } from "@/api/quiz";
import type { OptionLetter, WrongQuestion } from "@/types/quiz";
import {
  AppButton,
  AppCard,
  AppEmpty,
  AppIcon,
  AppPageHeader,
  AppStatusTag,
} from "@/components";

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const items = ref<WrongQuestion[]>([]);
const expanded = ref<Set<string>>(new Set());

function itemKey(it: WrongQuestion): string {
  return `${it.question_id}-${it.attempt_id}`;
}

function toggle(it: WrongQuestion): void {
  const key = itemKey(it);
  if (expanded.value.has(key)) expanded.value.delete(key);
  else expanded.value.add(key);
  expanded.value = new Set(expanded.value);
}

function isOpen(it: WrongQuestion): boolean {
  return expanded.value.has(itemKey(it));
}

async function load(): Promise<void> {
  loading.value = true;
  try {
    items.value = await quizApi.listWrong();
  } catch {
    items.value = [];
  } finally {
    loading.value = false;
  }
}

function toKb(entryId: string | null): void {
  if (!entryId) return;
  void router.push({
    name: "kb-detail",
    params: { entry_id: entryId },
    query: { from: "quiz-wrong" },
  });
}

function backToList(): void {
  if (route.query.return_to === "student-profile") {
    void router.push({ name: "student-profile" });
    return;
  }
  void router.push({ name: "quiz-entry" });
}

function formatDate(d: string): string {
  if (!d) return "—";
  const dt = new Date(d);
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(dt);
}

const OPTS: readonly OptionLetter[] = ["A", "B", "C", "D"];

onMounted(load);
</script>

<template>
  <div class="quiz-wrong">
    <AppPageHeader
      badge="UC-05 错题本"
      title="我的错题本"
      :subtitle="`最近 100 条答错的题目（共 ${items.length} 条）。点击标题展开详情。`"
    >
      <template #actions>
        <AppButton variant="ghost" size="md" @click="backToList">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
      </template>
    </AppPageHeader>

    <div v-if="loading" class="quiz-wrong__loading">
      <AppIcon name="loader" :size="22" class="quiz-wrong__spin" />
      加载中…
    </div>

    <AppCard v-else-if="items.length === 0" padding="md">
      <AppEmpty
        title="还没有错题"
        hint="继续保持！可以从安全测验入口开始一轮新的随机练习。"
        illustration="default"
      />
    </AppCard>

    <ul v-else class="quiz-wrong__list">
      <li
        v-for="(it, idx) in items"
        :key="itemKey(it)"
        class="quiz-wrong__item"
        :class="{ 'quiz-wrong__item--open': isOpen(it) }"
      >
        <span class="quiz-wrong__item-corner" aria-hidden="true" />

        <button
          type="button"
          class="quiz-wrong__row"
          :aria-expanded="isOpen(it)"
          @click="toggle(it)"
        >
          <span class="quiz-wrong__item-index">{{ idx + 1 }}</span>
          <span class="quiz-wrong__item-title">{{ it.content }}</span>
          <span class="quiz-wrong__item-time">
            <AppIcon name="clock" :size="12" />
            {{ formatDate(it.wrong_at) }}
          </span>
          <span class="quiz-wrong__chevron" aria-hidden="true">
            <AppIcon name="chevron-right" :size="16" />
          </span>
        </button>

        <div v-if="isOpen(it)" class="quiz-wrong__detail">
          <ul class="quiz-wrong__opts">
            <li
              v-for="opt in OPTS"
              :key="opt"
              class="quiz-wrong__opt"
              :class="{
                'quiz-wrong__opt--correct': it.correct_answer === opt,
                'quiz-wrong__opt--chosen-wrong':
                  it.chosen_answer === opt &&
                  it.chosen_answer !== it.correct_answer,
              }"
            >
              <span class="quiz-wrong__opt-letter">{{ opt }}</span>
              <span class="quiz-wrong__opt-text">
                {{
                  it[
                    `option_${opt.toLowerCase()}` as
                      | "option_a"
                      | "option_b"
                      | "option_c"
                      | "option_d"
                  ]
                }}
              </span>
              <AppIcon
                v-if="it.correct_answer === opt"
                name="circle-check"
                :size="14"
                class="quiz-wrong__opt-icon quiz-wrong__opt-icon--correct"
              />
              <AppIcon
                v-else-if="
                  it.chosen_answer === opt &&
                  it.chosen_answer !== it.correct_answer
                "
                name="circle-x"
                :size="14"
                class="quiz-wrong__opt-icon quiz-wrong__opt-icon--wrong"
              />
            </li>
          </ul>

          <div class="quiz-wrong__meta">
            <AppStatusTag
              status="danger"
              :text="`你选：${it.chosen_answer ?? '未作答'}`"
            />
            <AppStatusTag status="success" :text="`正确：${it.correct_answer}`" />
          </div>

          <div v-if="it.explanation" class="quiz-wrong__explain">
            <AppIcon name="info" :size="14" />
            <div>
              <strong>解析</strong>
              <p>{{ it.explanation }}</p>
            </div>
          </div>

          <footer class="quiz-wrong__actions">
            <AppButton
              v-if="it.knowledge_entry_id"
              variant="primary"
              size="sm"
              @click="toKb(it.knowledge_entry_id)"
            >
              <AppIcon name="book-open" :size="13" />
              跳转知识库学习
              <AppIcon name="arrow-right" :size="13" />
            </AppButton>
            <span v-else class="quiz-wrong__no-kb">
              <AppIcon name="info" :size="12" />
              本题暂未关联知识库
            </span>
          </footer>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.quiz-wrong {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── 加载状态 ── */
.quiz-wrong__loading {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.quiz-wrong__spin {
  animation: quiz-wrong-spin 1s linear infinite;
}

@keyframes quiz-wrong-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── 错题列表 ── */
.quiz-wrong__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.quiz-wrong__item {
  position: relative;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  overflow: hidden;
  transition:
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
}

.quiz-wrong__item:hover {
  border-color: var(--color-brand-300);
  box-shadow: var(--shadow-mid);
}

.quiz-wrong__item--open {
  border-color: var(--color-brand-400);
  box-shadow: var(--shadow-mid);
}

.quiz-wrong__item-corner {
  position: absolute;
  top: 0;
  left: 0;
  width: 16px;
  height: 16px;
  border-top: 2px solid var(--color-gold-400);
  border-left: 2px solid var(--color-gold-400);
  border-top-left-radius: var(--radius-lg);
  pointer-events: none;
  z-index: 1;
}

/* ── 折叠行（仅标题） ── */
.quiz-wrong__row {
  display: grid;
  grid-template-columns: 28px 1fr auto 20px;
  gap: var(--space-3);
  align-items: center;
  width: 100%;
  padding: var(--space-3) var(--space-4) var(--space-3) var(--space-5);
  background: transparent;
  border: 0;
  cursor: pointer;
  font: inherit;
  color: inherit;
  text-align: left;
  transition: background var(--duration-fast) var(--easing-out);
}

.quiz-wrong__row:hover {
  background: var(--color-bg-soft);
}

.quiz-wrong__item-index {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  font-size: 12px;
  font-weight: var(--font-weight-bold);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-family-mono);
}

.quiz-wrong__item-title {
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.quiz-wrong__item-time {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.quiz-wrong__chevron {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  transition: transform var(--duration-base) var(--easing-out);
}

.quiz-wrong__item--open .quiz-wrong__chevron {
  transform: rotate(90deg);
  color: var(--color-brand-600);
}

/* ── 展开的详情区 ── */
.quiz-wrong__detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: 0 var(--space-5) var(--space-4);
  border-top: 1px dashed var(--color-border);
  margin-top: 0;
  padding-top: var(--space-4);
  animation: quiz-wrong-expand var(--duration-base) var(--easing-out);
}

@keyframes quiz-wrong-expand {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── 选项列表 ── */
.quiz-wrong__opts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.quiz-wrong__opt {
  display: grid;
  grid-template-columns: 24px 1fr 16px;
  gap: var(--space-2);
  align-items: center;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: var(--color-bg-soft);
  font-size: var(--font-size-sm);
  color: var(--color-text);
}

.quiz-wrong__opt-letter {
  width: 24px;
  height: 24px;
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
}

.quiz-wrong__opt-text {
  min-width: 0;
}

.quiz-wrong__opt--correct {
  background: rgb(46 125 50 / 8%);
  border-color: rgb(46 125 50 / 28%);
  color: var(--color-success);
  font-weight: var(--font-weight-semibold);
}

.quiz-wrong__opt--correct .quiz-wrong__opt-letter {
  background: var(--color-success);
  color: #fff;
  border-color: transparent;
}

.quiz-wrong__opt--chosen-wrong {
  background: rgb(198 40 40 / 8%);
  border-color: rgb(198 40 40 / 28%);
  color: var(--color-danger);
  text-decoration: line-through;
}

.quiz-wrong__opt--chosen-wrong .quiz-wrong__opt-letter {
  background: var(--color-danger);
  color: #fff;
  border-color: transparent;
  text-decoration: none;
}

.quiz-wrong__opt-icon--correct {
  color: var(--color-success);
}

.quiz-wrong__opt-icon--wrong {
  color: var(--color-danger);
}

/* ── 状态标签 ── */
.quiz-wrong__meta {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

/* ── 解析区域 ── */
.quiz-wrong__explain {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(230 179 73 / 10%);
  border: 1px dashed rgb(160 120 35 / 40%);
  align-items: flex-start;
}

.quiz-wrong__explain svg {
  color: var(--color-gold-500);
  flex-shrink: 0;
  margin-top: 2px;
}

.quiz-wrong__explain strong {
  display: block;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gold-700);
  letter-spacing: 0.04em;
  margin-bottom: 2px;
}

.quiz-wrong__explain p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text);
  line-height: 1.65;
}

/* ── 底部操作 ── */
.quiz-wrong__actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-top: var(--space-2);
  border-top: 1px dashed var(--color-border);
}

.quiz-wrong__no-kb {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}
</style>