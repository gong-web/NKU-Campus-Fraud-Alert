<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { quizApi } from "@/api/quiz";
import type { QuizHistoryItem, QuizType } from "@/types/quiz";
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
const items = ref<QuizHistoryItem[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(20);
const typeFilter = ref<"" | QuizType>("");

const TYPE_OPTIONS: { value: "" | QuizType; label: string }[] = [
  { value: "", label: "全部" },
  { value: "RANDOM", label: "随机练习" },
  { value: "ASSIGNED", label: "指定测验" },
];

const filtered = computed<QuizHistoryItem[]>(() => {
  if (!typeFilter.value) return items.value;
  return items.value.filter((it) => it.quiz_type === typeFilter.value);
});

const passCount = computed<number>(
  () => filtered.value.filter((it) => it.is_pass).length,
);

const avgScore = computed<number>(() => {
  if (filtered.value.length === 0) return 0;
  const sum = filtered.value.reduce((acc, it) => acc + it.score, 0);
  return Math.round(sum / filtered.value.length);
});

async function load(): Promise<void> {
  loading.value = true;
  try {
    const r = await quizApi.listHistory({ page: page.value, size: size.value });
    items.value = r.items;
    total.value = r.total;
  } catch {
    items.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
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

function quizTypeLabel(t: QuizType): string {
  return t === "RANDOM" ? "随机练习" : "指定测验";
}

function reviewWrong(): void {
  void router.push({ name: "quiz-wrong" });
}

function backToProfile(): void {
  void router.push({ name: "student-profile" });
}

function startNew(): void {
  void router.push({ name: "quiz-entry" });
}

onMounted(load);
</script>

<template>
  <div class="quiz-history">
    <AppPageHeader
      title="测验历史记录"
      :subtitle="`共完成 ${total} 次测验，累计通过 ${passCount} 次，平均得分 ${avgScore} 分。`"
    >
      <template #actions>
        <AppButton variant="ghost" size="md" @click="backToProfile">
          <AppIcon name="arrow-left" :size="14" />
          返回个人中心
        </AppButton>
        <AppButton variant="ghost" size="md" @click="reviewWrong">
          <AppIcon name="book-open" :size="14" />
          我的错题本
        </AppButton>
        <AppButton variant="primary" size="md" @click="startNew">
          <AppIcon name="sparkles" :size="14" />
          开始新测验
        </AppButton>
      </template>
    </AppPageHeader>

    <!-- 筛选栏 -->
    <div class="quiz-history__filter">
      <button
        v-for="opt in TYPE_OPTIONS"
        :key="opt.value || 'all'"
        type="button"
        class="quiz-history__filter-btn"
        :class="{ active: typeFilter === opt.value }"
        @click="typeFilter = opt.value"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- 列表 -->
    <AppCard padding="none">
      <div v-if="loading" class="quiz-history__loading">
        <AppIcon name="loader" :size="22" class="quiz-history__spin" />
        加载中…
      </div>

      <div v-else-if="filtered.length === 0" class="quiz-history__empty-wrap">
        <AppEmpty
          title="还没有测验记录"
          hint="先去做一次随机练习吧"
          illustration="default"
        />
        <AppButton variant="primary" @click="startNew">
          <AppIcon name="sparkles" :size="14" />
          立即开始
        </AppButton>
      </div>

      <table v-else class="quiz-history__table">
        <thead>
          <tr>
            <th>测验类型</th>
            <th>测验标题</th>
            <th>得分</th>
            <th>正确数</th>
            <th>结果</th>
            <th>提交时间</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="it in filtered"
            :key="it.attempt_id"
            class="quiz-history__row"
          >
            <td>
              <span
                class="quiz-history__type-badge"
                :class="`quiz-history__type-badge--${it.quiz_type.toLowerCase()}`"
              >
                {{ quizTypeLabel(it.quiz_type) }}
              </span>
            </td>
            <td class="quiz-history__title">{{ it.quiz_title }}</td>
            <td>
              <span
                class="quiz-history__score"
                :class="{ 'quiz-history__score--pass': it.is_pass }"
              >
                {{ it.score }}
                <small>/ {{ it.pass_score }} 分及格</small>
              </span>
            </td>
            <td class="quiz-history__correct">
              {{ it.correct_count }} / {{ it.total_count }}
            </td>
            <td>
              <AppStatusTag
                :status="it.is_pass ? 'success' : 'danger'"
                :text="it.is_pass ? '已通过' : '未通过'"
              />
            </td>
            <td>{{ formatDate(it.submitted_at) }}</td>
          </tr>
        </tbody>
      </table>
    </AppCard>

    <!-- 分页 -->
    <div v-if="total > size" class="quiz-history__pagination">
      <AppButton
        variant="ghost"
        size="sm"
        :disabled="page <= 1"
        @click="
          page--;
          load();
        "
      >
        上一页
      </AppButton>
      <span>{{ page }} / {{ Math.ceil(total / size) }}</span>
      <AppButton
        variant="ghost"
        size="sm"
        :disabled="page >= Math.ceil(total / size)"
        @click="
          page++;
          load();
        "
      >
        下一页
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.quiz-history {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── 筛选栏 ── */
.quiz-history__filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.quiz-history__filter-btn {
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-out);
}

.quiz-history__filter-btn:hover,
.quiz-history__filter-btn.active {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
}

/* ── 加载 / 空态 ── */
.quiz-history__loading {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.quiz-history__spin {
  animation: quiz-history-spin 1s linear infinite;
}

@keyframes quiz-history-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.quiz-history__empty-wrap {
  padding: var(--space-6) 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

/* ── 表格 ── */
.quiz-history__table {
  width: 100%;
  border-collapse: collapse;
}

.quiz-history__table th {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.quiz-history__row td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
}

.quiz-history__row:hover {
  background: var(--color-bg-soft);
}

.quiz-history__type-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
}

.quiz-history__type-badge--random {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
}

.quiz-history__type-badge--assigned {
  background: var(--color-brand-50);
  color: var(--color-brand-700);
}

.quiz-history__title {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-strong);
}

.quiz-history__score {
  font-family: var(--font-family-mono);
  font-weight: var(--font-weight-bold);
  color: var(--color-danger);
  font-size: var(--font-size-md);
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
}

.quiz-history__score--pass {
  color: var(--color-success);
}

.quiz-history__score small {
  font-family: inherit;
  font-size: 10px;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-tertiary);
}

.quiz-history__correct {
  font-family: var(--font-family-mono);
  color: var(--color-text-secondary);
}

/* ── 分页 ── */
.quiz-history__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
