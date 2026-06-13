<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { quizApi, QUIZ_STATUS_LABEL } from "@/api/quiz";
import type { QuizCompletionReport, QuizDetail } from "@/types/quiz";
import { ApiError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppInput,
  AppModal,
  AppPageHeader,
  AppStatusTag,
} from "@/components";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const quizId = String(route.params.quiz_id);
const loading = ref(false);
const quiz = ref<QuizDetail | null>(null);
const report = ref<QuizCompletionReport | null>(null);

const cancelOpen = ref(false);
const cancelReason = ref("");
const cancelling = ref(false);

const isDeptReviewer = computed<boolean>(() => {
  const me = auth.me;
  return Boolean(me && me.role_code === "REVIEWER" && me.role_level === 1);
});

const visibleReport = computed<QuizCompletionReport | null>(() => {
  if (!report.value) return null;

  // 学院辅导员 / 院系审核员：只展示本院系
  if (isDeptReviewer.value) {
    const me = auth.me;
    const deptId = me?.department_id;
    if (!deptId) return report.value;
    const mine = report.value.by_department.find((d) => d.dept_id === deptId);
    const totalTargets = mine?.total_targets ?? 0;
    const submittedCount = mine?.submitted_count ?? 0;
    const passRate = mine?.pass_rate ?? 0;
    const avgScore = mine?.avg_score ?? 0;
    return {
      ...report.value,
      total_targets: totalTargets,
      submitted_count: submittedCount,
      completion_rate: totalTargets ? submittedCount / totalTargets : 0,
      pass_rate: passRate,
      avg_score: avgScore,
      by_department: mine ? [mine] : [],
    };
  }

  return report.value;
});

async function load(): Promise<void> {
  loading.value = true;
  try {
    await auth.fetchMe();
    const [d, r] = await Promise.all([
      quizApi.getAdminQuiz(quizId),
      quizApi.report(quizId),
    ]);
    quiz.value = d;
    report.value = r;
  } catch {
    quiz.value = null;
    report.value = null;
  } finally {
    loading.value = false;
  }
}

async function downloadXlsx(): Promise<void> {
  try {
    await quizApi.downloadReport(quizId);
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "下载失败");
  }
}

function openCancel(): void {
  cancelReason.value = "";
  cancelOpen.value = true;
}

async function confirmCancel(): Promise<void> {
  const reason = cancelReason.value.trim();
  if (reason.length < 1) {
    ElMessage.warning("请输入撤回原因");
    return;
  }
  cancelling.value = true;
  try {
    await quizApi.cancel(quizId, { reason });
    ElMessage.success("已撤回");
    cancelOpen.value = false;
    await load();
  } catch (e) {
    ElMessage.error(e instanceof ApiError ? e.message : "撤回失败");
  } finally {
    cancelling.value = false;
  }
}

function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function quizStatusTone(s: string): "success" | "warning" | "neutral" {
  if (s === "ACTIVE") return "success";
  if (s === "FINISHED") return "warning";
  return "neutral";
}

onMounted(load);
</script>

<template>
  <div class="report">
    <!-- 加载失败态 -->
    <AppCard v-if="!loading && !visibleReport" padding="md" class="report__error">
      <div class="report__error-inner">
        <AppIcon name="activity" :size="36" class="report__error-icon" />
        <p>测验数据加载失败</p>
        <AppButton variant="ghost" size="md" @click="router.push({ name: 'admin-quiz-list' })">
          <AppIcon name="arrow-left" :size="14" />
          返回列表
        </AppButton>
      </div>
    </AppCard>

    <template v-else-if="visibleReport && quiz">
      <!-- 页头 -->
      <AppPageHeader
        :title="quiz.title"
        :subtitle="`截止：${quiz.deadline_at?.slice(0, 16).replace('T', ' ') || '—'} · 题目数：${quiz.question_count} · 及格分：${quiz.pass_score}`"
      >
        <template #actions>
          <AppButton variant="ghost" size="md" @click="router.push({ name: 'admin-quiz-list' })">
            <AppIcon name="arrow-left" :size="14" />
            返回列表
          </AppButton>
          <AppStatusTag
            :status="quizStatusTone(quiz.status)"
            :text="QUIZ_STATUS_LABEL[quiz.status] || quiz.status"
          />
          <AppButton variant="secondary" size="md" @click="downloadXlsx">
            <AppIcon name="download" :size="14" />
            导出 Excel
          </AppButton>
          <AppButton
            v-if="quiz.status === 'ACTIVE'"
            variant="danger"
            size="md"
            @click="openCancel"
          >
            <AppIcon name="alert-triangle" :size="14" />
            撤回测验
          </AppButton>
        </template>
      </AppPageHeader>

      <!-- KPI 卡片 -->
      <div class="report__kpis">
        <AppCard padding="md" class="report__kpi">
          <div class="report__kpi-val">{{ visibleReport.submitted_count }} <span class="report__kpi-denom">/ {{ visibleReport.total_targets }}</span></div>
          <div class="report__kpi-label">完成 / 目标</div>
        </AppCard>
        <AppCard padding="md" class="report__kpi">
          <div class="report__kpi-val">{{ pct(visibleReport.completion_rate) }}</div>
          <div class="report__kpi-label">完成率</div>
        </AppCard>
        <AppCard padding="md" class="report__kpi">
          <div class="report__kpi-val">{{ pct(visibleReport.pass_rate) }}</div>
          <div class="report__kpi-label">及格率</div>
        </AppCard>
        <AppCard padding="md" class="report__kpi">
          <div class="report__kpi-val">{{ visibleReport.avg_score.toFixed(1) }}</div>
          <div class="report__kpi-label">平均分</div>
        </AppCard>
      </div>

      <!-- 院系完成情况 -->
      <AppCard padding="md">
        <template #header>
          <span class="report__section-title">{{ isDeptReviewer ? '本学院完成情况' : '各院系完成情况' }}</span>
        </template>

        <div v-if="visibleReport.by_department.length === 0" class="report__empty">暂无院系数据</div>

        <!-- 条形图 -->
        <div v-else class="report__bars">
          <div v-for="d in visibleReport.by_department" :key="d.dept_id" class="report__bar-row">
            <span class="report__bar-label">{{ d.dept_name }}</span>
            <div class="report__bar-wrap">
              <div class="report__bar" :style="{ width: pct(d.completion_rate) }" />
              <span class="report__bar-text">{{ pct(d.completion_rate) }} · {{ d.submitted_count }}/{{ d.total_targets }}</span>
            </div>
          </div>
        </div>

        <!-- 明细表 -->
        <div class="report__table-wrap">
          <table class="report__table">
            <colgroup>
              <col class="report__col-dept" />
              <col class="report__col-num" />
              <col class="report__col-num" />
              <col class="report__col-num" />
              <col class="report__col-num" />
              <col class="report__col-num" />
              <col class="report__col-num" />
            </colgroup>
            <thead>
              <tr>
                <th class="report__th-dept">院系</th>
                <th class="report__th-num">目标</th>
                <th class="report__th-num">已提交</th>
                <th class="report__th-num">完成率</th>
                <th class="report__th-num">及格</th>
                <th class="report__th-num">及格率</th>
                <th class="report__th-num">平均分</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in visibleReport.by_department" :key="d.dept_id" class="report__row">
                <td class="report__dept-cell">{{ d.dept_name }}</td>
                <td class="report__num-cell">{{ d.total_targets }}</td>
                <td class="report__num-cell">{{ d.submitted_count }}</td>
                <td class="report__num-cell report__num-cell--accent">{{ pct(d.completion_rate) }}</td>
                <td class="report__num-cell">{{ d.pass_count }}</td>
                <td class="report__num-cell report__num-cell--accent">{{ pct(d.pass_rate) }}</td>
                <td class="report__num-cell">{{ d.avg_score.toFixed(1) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AppCard>
    </template>

    <!-- 撤回测验弹窗 -->
    <AppModal v-model="cancelOpen" title="撤回测验" width="480px">
      <div class="report__cancel">
        <div class="report__cancel-icon">
          <AppIcon name="alert-triangle" :size="24" />
        </div>
        <div class="report__cancel-body">
          <p class="report__cancel-title">撤回后学生将无法继续作答</p>
          <p class="report__cancel-desc">
            撤回原因仅管理员可见，学生侧只看到状态变化。已提交的作答记录会保留。
          </p>
        </div>
      </div>
      <AppInput
        v-model="cancelReason"
        type="textarea"
        :rows="3"
        :maxlength="200"
        label="撤回原因"
        :required="true"
        placeholder="例如：题目错误，需要修正后重新发起"
      />
      <template #footer>
        <AppButton variant="ghost" @click="cancelOpen = false">取消</AppButton>
        <AppButton variant="danger" :loading="cancelling" @click="confirmCancel">
          <AppIcon name="alert-triangle" :size="13" />
          确认撤回
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.report {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── 错误态 ── */
.report__error {
  min-height: 240px;
}

.report__error-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  min-height: 200px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.report__error-icon {
  color: var(--color-brand-400);
  opacity: 0.6;
}

/* ── KPI 格子 ── */
.report__kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-3);
}

@media (max-width: 640px) {
  .report__kpis { grid-template-columns: repeat(2, 1fr); }
}

.report__kpi {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.report__kpi-val {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-brand-600);
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

.report__kpi-denom {
  font-size: 16px;
  font-weight: 400;
  color: var(--color-text-secondary);
}

.report__kpi-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
}

/* ── 章节标题 ── */
.report__section-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

/* ── 条形图 ── */
.report__bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.report__bar-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: var(--space-3);
  align-items: center;
  font-size: var(--font-size-xs);
}

.report__bar-label {
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report__bar-wrap {
  position: relative;
  background: var(--color-bg-soft);
  height: 22px;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.report__bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: var(--gradient-brand);
  border-radius: var(--radius-sm);
  transition: width 0.4s var(--easing-out);
}

.report__bar-text {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  color: var(--color-text-strong);
  font-variant-numeric: tabular-nums;
  font-weight: var(--font-weight-semibold);
  mix-blend-mode: multiply;
}

/* ── 明细表格 ── */
.report__table-wrap {
  overflow-x: auto;
}

.report__table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.report__col-dept { width: 28%; }
.report__col-num { width: 12%; }

.report__table th,
.report__table td {
  padding: var(--space-3) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  white-space: nowrap;
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report__th-dept {
  text-align: left !important;
}

.report__table thead th {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--color-bg-soft);
}

.report__th-num {
  text-align: left !important;
}

.report__row {
  transition: background var(--duration-fast) var(--easing-out);
}

.report__row:hover {
  background: var(--color-bg-soft);
}

.report__dept-cell {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.report__num-cell {
  text-align: left;
  font-family: var(--font-family-mono);
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
}

.report__num-cell--accent {
  color: var(--color-brand-600);
  font-weight: var(--font-weight-semibold);
}

.report__empty {
  color: var(--color-text-secondary);
  padding: var(--space-4);
  text-align: center;
  font-size: var(--font-size-sm);
}

/* ── 撤回弹窗 ── */
.report__cancel {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  margin-bottom: var(--space-4);
}

.report__cancel-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.report__cancel-body {
  flex: 1;
  min-width: 0;
}

.report__cancel-title {
  margin: 0 0 var(--space-1);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.report__cancel-desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.65;
}
</style>
