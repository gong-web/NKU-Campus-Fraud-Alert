<!-- QuizEntryPage.vue (统一风格后) -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { quizApi, QUIZ_STATUS_LABEL } from "@/api/quiz";
import type { QuizListItem } from "@/types/quiz";
import { ApiError } from "@/api/http";
import {
  AppButton,
  AppCard,
  AppEmpty,
  AppIcon,
  AppPageHeader,
  AppStatusTag,
} from "@/components";

const router = useRouter();

const loading = ref(false);
const startingRandom = ref(false);
const assigned = ref<QuizListItem[]>([]);

function formatDeadline(d: string | null): string {
  if (!d) return "无截止";
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

function quizStatusTone(
  s: QuizListItem["status"],
): "success" | "warning" | "neutral" {
  if (s === "ACTIVE") return "success";
  if (s === "FINISHED") return "warning";
  return "neutral";
}

function myStateLabel(it: QuizListItem): string {
  if (it.my_attempt_status === "SUBMITTED")
    return `已提交 · ${it.my_score ?? 0} 分`;
  if (it.my_attempt_status === "IN_PROGRESS") return "进行中";
  return "未开始";
}

async function load(): Promise<void> {
  loading.value = true;
  try {
    assigned.value = await quizApi.listAssigned();
  } catch {
    assigned.value = [];
  } finally {
    loading.value = false;
  }
}

async function startRandom(): Promise<void> {
  startingRandom.value = true;
  try {
    const out = await quizApi.startRandom();
    await router.push({
      name: "quiz-answer",
      params: { attempt_id: out.attempt_id },
      state: { start: JSON.parse(JSON.stringify(out)) },
    });
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "启动随机练习失败");
  } finally {
    startingRandom.value = false;
  }
}

async function startAssigned(it: QuizListItem): Promise<void> {
  if (it.status !== "ACTIVE") {
    ElMessage.warning("该测验已不可作答");
    return;
  }
  if (it.my_attempt_status === "SUBMITTED") {
    ElMessage.info("你已提交过本次测验");
    return;
  }
  try {
    const out = await quizApi.startAssigned(it.quiz_id);
    await router.push({
      name: "quiz-answer",
      params: { attempt_id: out.attempt_id },
      state: { start: JSON.parse(JSON.stringify(out)) },
    });
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "开始测验失败");
  }
}

function openWrong(): void {
  void router.push({ name: "quiz-wrong" });
}

onMounted(load);
</script>

<template>
  <div class="quiz-entry">
    <AppPageHeader
      badge="UC-05 / UC-09"
      title="安全测验"
      :subtitle="`检验你的反诈识别能力。答错的题目会自动加入错题本，并关联到反诈知识库相关条目。`"
    />

    <!-- 顶部双卡：随机练习 + 我的错题本入口（统一卡片样式） -->
    <div class="quiz-entry__quick">
      <article class="quiz-entry__card quiz-entry__card--quick">
        <span class="quiz-entry__card-corner" aria-hidden="true" />
        <div class="quiz-entry__card-body">
          <div class="quiz-entry__card-tag">
            <AppIcon name="sparkles" :size="12" />
            随机练习
          </div>
          <h3 class="quiz-entry__card-title">从题库随机抽 10 题</h3>
          <p class="quiz-entry__card-summary">
            覆盖刷单返利、冒充公检法、虚假兼职等六大类常见诈骗手法。60 分及格，答错自动入错题本。
          </p>
          <div class="quiz-entry__card-meta">
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="list-checks" :size="13" />
              10 道题
            </span>
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="circle-check" :size="13" />
              60 分及格
            </span>
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="clock" :size="13" />
              约 5 分钟
            </span>
          </div>
        </div>
        <div class="quiz-entry__card-action">
          <AppButton
            variant="primary"
            size="md"
            :loading="startingRandom"
            @click="startRandom"
          >
            <AppIcon name="sparkles" :size="14" />
            开始随机练习
          </AppButton>
        </div>
      </article>

      <article class="quiz-entry__card quiz-entry__card--quick" @click="openWrong">
        <span class="quiz-entry__card-corner" aria-hidden="true" />
        <div class="quiz-entry__card-body">
          <div class="quiz-entry__card-tag">
            <AppIcon name="book-open" :size="12" />
            我的错题本
          </div>
          <h3 class="quiz-entry__card-title">复盘最近的错题</h3>
          <p class="quiz-entry__card-summary">
            最近 100 条答错的题目集中复盘，并跳转到对应的反诈知识库条目深入学习。
          </p>
          <div class="quiz-entry__card-meta">
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="info" :size="13" />
              含解析
            </span>
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="arrow-right" :size="13" />
              跳转知识库
            </span>
          </div>
        </div>
        <div class="quiz-entry__card-action">
          <AppButton variant="secondary" size="md">
            <AppIcon name="book-open" :size="14" />
            查看错题本
          </AppButton>
        </div>
      </article>
    </div>

    <!-- 指定测验区段 -->
    <section class="quiz-entry__assigned">
      <div class="quiz-entry__section-head">
        <h3 class="quiz-entry__section-title">
          <AppIcon name="clipboard-list" :size="18" />
          指定测验
        </h3>
        <small>管理员发起的限时测验，按截止时间排序</small>
      </div>

      <div v-if="loading" class="quiz-entry__loading">
        <AppIcon name="loader" :size="22" class="quiz-entry__spin" />
        加载中…
      </div>
      <AppCard v-else-if="assigned.length === 0" padding="md">
        <AppEmpty
          title="暂无指定测验"
          hint="先做几道随机练习保持手感吧"
          illustration="default"
        />
      </AppCard>
      <div v-else class="quiz-entry__grid">
        <article
          v-for="it in assigned"
          :key="it.quiz_id"
          class="quiz-entry__card quiz-entry__card--assigned"
          @click="startAssigned(it)"
        >
          <span class="quiz-entry__card-corner" aria-hidden="true" />
          <div class="quiz-entry__card-tag">
            <AppIcon name="clipboard-list" :size="12" />
            指定测验
          </div>
          <div class="quiz-entry__card-head">
            <h4 class="quiz-entry__card-title">{{ it.title }}</h4>
            <AppStatusTag
              :status="quizStatusTone(it.status)"
              :text="QUIZ_STATUS_LABEL[it.status] || it.status"
            />
          </div>
          <p class="quiz-entry__card-summary">
            我的状态：{{ myStateLabel(it) }}
          </p>
          <div class="quiz-entry__card-meta">
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="list-checks" :size="13" />
              {{ it.question_count }} 题
            </span>
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="circle-check" :size="13" />
              {{ it.pass_score }} 分及格
            </span>
            <span class="quiz-entry__card-meta-cell">
              <AppIcon name="clock" :size="13" />
              截止：{{ formatDeadline(it.deadline_at) }}
            </span>
          </div>
          <div class="quiz-entry__card-action">
            <AppButton
              variant="primary"
              size="sm"
              :disabled="
                it.status !== 'ACTIVE' || it.my_attempt_status === 'SUBMITTED'
              "
              @click.stop="startAssigned(it)"
            >
              {{
                it.my_attempt_status === "IN_PROGRESS" ? "继续作答" : "开始作答"
              }}
              <AppIcon name="arrow-right" :size="13" />
            </AppButton>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.quiz-entry {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── 顶部双卡 ────────────────────────────────────────── */
.quiz-entry__quick {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* ── 统一卡片样式（与 KnowledgeListPage 完全一致） ── */
.quiz-entry__card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  cursor: pointer;
  transition:
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
  overflow: hidden;
}

.quiz-entry__card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-mid);
  border-color: var(--color-brand-300);
}

.quiz-entry__card-corner {
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

.quiz-entry__card-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  font-size: 10.5px;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
  width: fit-content;
}

.quiz-entry__card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.quiz-entry__card-title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
  line-height: 1.4;
  flex: 1;
}

.quiz-entry__card-summary {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.quiz-entry__card-meta {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--color-border);
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.quiz-entry__card-meta-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.quiz-entry__card-action {
  margin-top: var(--space-2);
}

/* ── 快捷卡片横向布局 ── */
.quiz-entry__card--quick {
  flex-direction: row;
  align-items: center;
  gap: var(--space-5);
}

.quiz-entry__card--quick .quiz-entry__card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.quiz-entry__card--quick .quiz-entry__card-meta {
  margin-top: 0;
}

.quiz-entry__card--quick .quiz-entry__card-action {
  flex-shrink: 0;
  margin-top: 0;
}

/* ── 指定测验网格布局（与知识库列表一致） ── */
.quiz-entry__assigned {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.quiz-entry__section-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: var(--space-1);
}

.quiz-entry__section-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
}

.quiz-entry__section-title svg {
  color: var(--color-brand-600);
}

.quiz-entry__section-head small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.quiz-entry__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-4);
}

.quiz-entry__card--assigned {
  cursor: pointer;
}

/* ── 加载状态（与知识库列表一致） ── */
.quiz-entry__loading {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.quiz-entry__spin {
  animation: quiz-entry-spin 1s linear infinite;
}

@keyframes quiz-entry-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
