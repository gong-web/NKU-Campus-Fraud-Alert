<script setup lang="ts">
import { computed, nextTick, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { JudicialDecryptOut } from "@/types/api";
import { judicialApi } from "@/api/judicial";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppInput,
  AppModal,
  AppPageHeader,
  AppStatusTag,
} from "@/components";

const form = reactive({
  report_id: "",
  judicial_doc_no: "",
  reason: "",
  related_case_no: "",
});
const submitting = ref<boolean>(false);
const decryptLogId = ref<string | null>(null);
const expiresAt = ref<string>("");
const remaining = ref<number>(0);
const reveal = ref<JudicialDecryptOut | null>(null);
const showConfirm = ref<boolean>(false);
const error = ref<string>("");
const windowCard = ref<HTMLElement | null>(null);
const revealCard = ref<HTMLElement | null>(null);
const isDemoMode = import.meta.env.DEV;

const demoPreset = {
  report_id: "990000000000000005",
  judicial_doc_no: "演示协查字〔2026〕第001号",
  reason: "演示核验匿名上报人的身份保护和授权查看流程",
  related_case_no: "2026-CS-900005",
};

const watermark = computed<string>(() => reveal.value?.watermark_text ?? "");
const remainingMM = computed<string>(() => {
  const m = Math.floor(remaining.value / 60);
  const s = remaining.value % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
});

let timer: number | undefined;

function startCountdown(toIso: string): void {
  expiresAt.value = toIso;
  if (timer) window.clearInterval(timer);

  const updateRemaining = (): void => {
    const left = Math.max(0, Math.floor((new Date(toIso).getTime() - Date.now()) / 1000));
    remaining.value = left;
    if (left === 0) {
      if (timer) window.clearInterval(timer);
      reveal.value = null;
    }
  };

  updateRemaining();
  timer = window.setInterval(updateRemaining, 1000) as unknown as number;
}

function fillDemoData(): void {
  Object.assign(form, demoPreset);
  error.value = "";
  ElMessage.success("已填入可直接演示的匿名案件数据");
}

function openConfirmation(): void {
  if (!/^\d+$/.test(form.report_id.trim())) {
    error.value = "请输入有效的数字事件编号";
    return;
  }
  if (!form.judicial_doc_no.trim()) {
    error.value = "请输入协查文书编号";
    return;
  }
  if (!form.reason.trim()) {
    error.value = "请输入申请理由";
    return;
  }
  error.value = "";
  showConfirm.value = true;
}

async function submit(): Promise<void> {
  error.value = "";
  showConfirm.value = false;
  submitting.value = true;
  try {
    const reportId = form.report_id.trim();
    if (!/^\d+$/.test(reportId)) {
      error.value = "事件编号必须是数字";
      submitting.value = false;
      return;
    }
    const r = await judicialApi.requestDecryption({
      report_id: reportId,
      judicial_doc_no: form.judicial_doc_no,
      reason: form.reason,
      related_case_no: form.related_case_no || undefined,
    });
    decryptLogId.value = r.decrypt_log_id;
    startCountdown(r.expires_at);
    reveal.value = null;
    ElMessage.success("申请已提交，5 分钟临时查看窗口已开启");
    await nextTick();
    windowCard.value?.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (e) {
    error.value = e instanceof Error ? e.message : "提交失败";
  } finally {
    submitting.value = false;
  }
}

async function revealNow(): Promise<void> {
  if (decryptLogId.value == null) return;
  try {
    reveal.value = await judicialApi.reveal(decryptLogId.value);
    ElMessage.success("身份信息已显示，本次查看已写入审计日志");
    await nextTick();
    revealCard.value?.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (e) {
    error.value = e instanceof Error ? e.message : "解密失败";
  }
}
</script>

<template>
  <div class="judicial-page">
    <AppPageHeader
      title="司法协助查询"
    />

    <!-- 危险提醒条 -->
    <div
      class="judicial-page__banner"
      role="alert"
    >
      <span class="judicial-page__banner-icon">
        <AppIcon
          name="shield-alert"
          :size="20"
        />
      </span>
      <div class="judicial-page__banner-body">
        <strong>用于依法核验匿名上报人身份，申请和查看都会留下记录</strong>
        <p>
          申请成功后，仅当前申请人可在 5 分钟内查看一次身份信息，超时需重新申请。
          请确保已取得保卫处或学生处的<strong>书面同意</strong>，并按照协查文书号规范填写。
        </p>
      </div>
      <span class="judicial-page__banner-stamp">敏感</span>
    </div>

    <div class="judicial-page__grid">
      <!-- 表单 -->
      <AppCard
        padding="lg"
        :corner="true"
        class="judicial-page__form-card"
      >
        <template #header>
          <div>
            <h3>申请协助解密</h3>
            <small>普通审核员始终看不到匿名身份，只有系统管理员可发起临时授权查看。</small>
          </div>
          <AppButton
            v-if="isDemoMode"
            variant="secondary"
            size="sm"
            @click="fillDemoData"
          >
            <AppIcon
              name="sparkles"
              :size="14"
            />
            填入演示数据
          </AppButton>
        </template>

        <form
          class="judicial-page__form"
          @submit.prevent="openConfirmation"
        >
          <AppInput
            v-model="form.report_id"
            label="事件编号"
            :required="true"
            placeholder="如 1234567890"
            hint="这是匿名上报记录的内部编号，不是案件编号。"
          />
          <AppInput
            v-model="form.judicial_doc_no"
            label="协查文书编号"
            :required="true"
            placeholder="如 公协字 [2026] 第 001 号"
            hint="请与纸质协查文书保持一致。"
          />
          <AppInput
            v-model="form.reason"
            label="申请理由"
            type="textarea"
            :rows="4"
            :required="true"
            placeholder="请简明描述办案场景，例如：受理 2026-CS-000123 案件，需核对匿名上报人身份以补全笔录。"
            :hint="`已输入 ${form.reason.length} 字`"
          />
          <AppInput
            v-model="form.related_case_no"
            label="关联案件编号（可选）"
            placeholder="如 2026-CS-000123"
          />

          <p
            v-if="error"
            class="judicial-page__error"
            role="alert"
          >
            <AppIcon
              name="alert-triangle"
              :size="14"
            />
            {{ error }}
          </p>

          <div class="judicial-page__form-actions">
            <span class="judicial-page__form-tip">
              <AppIcon
                name="lock"
                :size="12"
              />
              提交前需再次确认，申请动作会写入高敏审计日志。
            </span>
            <AppButton
              type="submit"
              variant="danger"
              size="lg"
              :loading="submitting"
            >
              <AppIcon
                name="scale"
                :size="16"
              />
              提交申请
            </AppButton>
          </div>
        </form>
      </AppCard>

      <!-- 流程提示 -->
      <AppCard
        padding="lg"
        class="judicial-page__flow"
      >
        <template #header>
          <div>
            <h3>解密流程</h3>
          </div>
        </template>
        <ol class="judicial-page__flow-list">
          <li>
            <span class="judicial-page__flow-no">01</span>
            <div>
              <strong>填写申请</strong>
              <small>事件编号、协查文书号、申请理由</small>
            </div>
          </li>
          <li>
            <span class="judicial-page__flow-no">02</span>
            <div>
              <strong>二次确认</strong>
              <small>核对申请依据并记录操作</small>
            </div>
          </li>
          <li>
            <span class="judicial-page__flow-no">03</span>
            <div>
              <strong>5 分钟解密窗口</strong>
              <small>仅本人可见，页面带有防泄密标识</small>
            </div>
          </li>
          <li>
            <span class="judicial-page__flow-no">04</span>
            <div>
              <strong>窗口关闭</strong>
              <small>再次查看需重新申请</small>
            </div>
          </li>
        </ol>
      </AppCard>
    </div>

    <!-- 解密窗口（已申请） -->
    <section
      v-if="decryptLogId != null"
      ref="windowCard"
    >
      <AppCard
        padding="lg"
        class="judicial-page__window"
      >
        <div class="judicial-page__window-grid">
          <div>
            <p class="judicial-page__window-eyebrow">
              解密窗口已开启
            </p>
            <p class="judicial-page__window-id">
              申请编号 <code>{{ decryptLogId }}</code>
            </p>
            <p class="judicial-page__window-meta">
              这 5 分钟是“临时查看权限”的有效期，不是等待 5 分钟。现在即可点击右侧按钮查看身份。
            </p>
          </div>
          <div class="judicial-page__window-timer">
            <span class="judicial-page__window-time">{{ remainingMM }}</span>
            <small>剩余时间</small>
            <AppStatusTag
              status="warning"
              :text="`${remaining} 秒`"
            />
          </div>
          <AppButton
            variant="primary"
            size="lg"
            @click="revealNow"
          >
            <AppIcon
              name="lock"
              :size="16"
            />
            查看匿名上报人身份
          </AppButton>
        </div>
      </AppCard>
    </section>

    <!-- 解密结果 -->
    <section
      v-if="reveal"
      ref="revealCard"
      role="region"
      aria-label="解密结果"
    >
      <AppCard
        padding="lg"
        class="judicial-page__reveal"
      >
        <div
          class="judicial-page__reveal-watermark"
          aria-hidden="true"
        >
          <template
            v-for="i in 10"
            :key="i"
          >
            <span>{{ watermark }}</span>
          </template>
        </div>
        <div class="judicial-page__reveal-body">
          <h3>上报人身份信息</h3>
          <p class="judicial-page__reveal-summary">
            匿名案件 <strong>{{ reveal.report_id }}</strong> 的身份核验结果如下。
          </p>
          <dl class="judicial-page__reveal-dl">
            <div>
              <dt>姓名</dt>
              <dd>{{ reveal.real_name }}</dd>
            </div>
            <div>
              <dt>学号/工号</dt>
              <dd class="font-mono">
                {{ reveal.cas_account }}
              </dd>
            </div>
          </dl>
          <p class="judicial-page__reveal-notice">
            <AppIcon
              name="shield-alert"
              :size="14"
            />
            本次查看已留下记录；离开页面后再次查看需重新申请。
          </p>
        </div>
      </AppCard>
    </section>

    <AppModal
      v-model="showConfirm"
      title="确认提交申请"
    >
      <div class="judicial-page__confirm">
        <p>
          即将创建一个<strong>仅当前账号可用</strong>的临时查看窗口，
          允许在 5 分钟内查看该匿名上报人的身份信息。
        </p>
        <ul>
          <li>
            <AppIcon
              name="shield-check"
              :size="14"
            />本次操作会留下记录
          </li>
          <li>
            <AppIcon
              name="shield-alert"
              :size="14"
            />系统会记录高敏告警日志
          </li>
          <li>
            <AppIcon
              name="lock"
              :size="14"
            />解密窗口仅有 5 分钟
          </li>
        </ul>
        <p class="judicial-page__confirm-q">
          是否继续？
        </p>
      </div>
      <template #footer>
        <AppButton
          variant="secondary"
          @click="showConfirm = false"
        >
          取消
        </AppButton>
        <AppButton
          variant="danger"
          @click="submit"
        >
          <AppIcon
            name="scale"
            :size="14"
          />
          确认提交
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.judicial-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── 危险条 ───────────────────────────────────────────────────── */
.judicial-page__banner {
  position: relative;
  display: grid;
  grid-template-columns: 44px 1fr auto;
  gap: var(--space-4);
  align-items: center;
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgb(198 40 40 / 8%), rgb(198 40 40 / 4%));
  border: 1px solid rgb(198 40 40 / 24%);
  border-left: 4px solid var(--color-danger);
  overflow: hidden;
}

.judicial-page__banner::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: var(--pattern-noise);
  background-size: 160px 160px;
  opacity: 0.12;
  mix-blend-mode: multiply;
  pointer-events: none;
}

.judicial-page__banner-icon {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--gradient-danger);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 16px -8px rgb(198 40 40 / 56%),
    inset 0 0 0 1px rgb(255 255 255 / 18%);
}

.judicial-page__banner-body {
  position: relative;
  min-width: 0;
}

.judicial-page__banner-body strong {
  display: block;
  font-size: var(--font-size-md);
  color: var(--color-danger);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.01em;
}

.judicial-page__banner-body p {
  margin: 4px 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text);
  line-height: 1.65;
}

.judicial-page__banner-body strong:last-child,
.judicial-page__banner-body p strong {
  display: inline;
  color: var(--color-text-strong);
}

.judicial-page__banner-stamp {
  position: relative;
  font-family: var(--font-family-serif);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.18em;
  padding: 4px 10px;
  background: var(--gradient-seal);
  color: #ffe9c4;
  border: 1.5px solid rgb(255 233 196 / 50%);
  border-radius: 4px;
  transform: rotate(-6deg);
  box-shadow:
    0 2px 0 rgb(31 8 11 / 60%),
    inset 0 0 0 1px rgb(255 233 196 / 18%);
  text-shadow: 0 1px 2px rgb(31 8 11 / 60%);
}

/* ── 双栏 ─────────────────────────────────────────────────────── */
.judicial-page__grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: var(--space-4);
}

@media (width <= 1024px) {
  .judicial-page__grid {
    grid-template-columns: 1fr;
  }
}

/* ── 表单 ─────────────────────────────────────────────────────── */
.judicial-page__form-card h3,
.judicial-page__flow h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.judicial-page__form-card :deep(.app-card__header) {
  align-items: center;
}

.judicial-page__form-card small,
.judicial-page__flow small {
  display: block;
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.judicial-page__step {
  font-family: var(--font-family-mono);
  font-size: 11px;
  letter-spacing: 0.18em;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  border: 1px solid rgb(134 38 51 / 14%);
}

.judicial-page__form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.judicial-page__form > :nth-child(3),
.judicial-page__form > :nth-child(4),
.judicial-page__form > :nth-child(5),
.judicial-page__form > :nth-child(6) {
  grid-column: 1 / -1;
}

@media (width <= 640px) {
  .judicial-page__form {
    grid-template-columns: 1fr;
  }
}

.judicial-page__error {
  margin: 0;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: rgb(198 40 40 / 6%);
  border: 1px solid rgb(198 40 40 / 22%);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.judicial-page__form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--color-border);
}

.judicial-page__form-tip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

/* ── 流程列表 ─────────────────────────────────────────────────── */
.judicial-page__flow-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

@media (width <= 1024px) {
  .judicial-page__flow-list {
    grid-template-columns: 1fr;
  }
}

.judicial-page__flow-list li {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: var(--space-2);
  align-items: center;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-bg-soft);
  border: 1px solid var(--color-border-soft);
  transition: all var(--duration-base) var(--easing-out);
}

.judicial-page__flow-list li:hover {
  border-color: var(--color-border-strong);
  background: var(--color-bg);
  transform: translateX(2px);
}

.judicial-page__flow-no {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--gradient-brand);
  color: #fff;
  font-family: var(--font-family-serif);
  font-weight: var(--font-weight-bold);
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.04em;
  box-shadow: 0 4px 8px -4px rgb(134 38 51 / 32%);
}

.judicial-page__flow-list strong {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.judicial-page__flow-list small {
  font-size: 11.5px;
  color: var(--color-text-secondary);
  margin-top: 1px;
  display: block;
}

/* ── 解密窗口 ─────────────────────────────────────────────────── */
.judicial-page__window {
  border-color: var(--color-warning);
  background:
    linear-gradient(180deg, rgb(239 108 0 / 4%), rgb(239 108 0 / 1%));
}

.judicial-page__window-grid {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: var(--space-5);
  align-items: center;
}

@media (width <= 768px) {
  .judicial-page__window-grid {
    grid-template-columns: 1fr;
  }
}

.judicial-page__window-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-weight: var(--font-weight-semibold);
}

.judicial-page__window-eyebrow .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-warning);
  animation: pulse-warn 1.6s ease-in-out infinite;
}

@keyframes pulse-warn {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.judicial-page__window-id {
  margin: var(--space-2) 0 0;
  font-size: var(--font-size-md);
  color: var(--color-text-strong);
}

.judicial-page__window-id code {
  font-family: var(--font-family-mono);
  background: var(--color-warning);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.04em;
  font-weight: var(--font-weight-semibold);
}

.judicial-page__window-meta {
  margin: var(--space-2) 0 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.judicial-page__window-timer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid rgb(239 108 0 / 32%);
}

.judicial-page__window-time {
  font-family: var(--font-family-mono);
  font-size: 32px;
  font-weight: var(--font-weight-bold);
  color: var(--color-warning);
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.judicial-page__window-timer small {
  font-size: 11px;
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
}

/* ── 解密结果 ─────────────────────────────────────────────────── */
.judicial-page__reveal {
  position: relative;
  overflow: hidden;
  border-color: var(--color-danger);
  user-select: none;
}

.judicial-page__reveal-watermark {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--space-7);
  pointer-events: none;
  opacity: 0.08;
  transform: rotate(-22deg);
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--color-danger);
  white-space: nowrap;
  overflow: hidden;
  z-index: 0;
  padding: var(--space-7);
}

.judicial-page__reveal-body {
  position: relative;
  z-index: 1;
}

.judicial-page__reveal-body h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  color: var(--color-danger);
}

.judicial-page__reveal-summary {
  margin: var(--space-2) 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.judicial-page__reveal-summary strong {
  color: var(--color-text-strong);
  font-family: var(--font-family-mono);
}

.judicial-page__reveal-dl {
  margin: var(--space-3) 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.judicial-page__reveal-dl > div {
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-soft);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.judicial-page__reveal-dl dt {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.judicial-page__reveal-dl dd {
  margin: 4px 0 0;
  font-size: var(--font-size-md);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.judicial-page__reveal-notice {
  margin: var(--space-3) 0 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--color-danger);
  padding: var(--space-2) var(--space-3);
  background: rgb(198 40 40 / 6%);
  border-radius: var(--radius-sm);
  border: 1px dashed rgb(198 40 40 / 32%);
}

/* ── 二次确认弹窗 ─────────────────────────────────────────────── */
.judicial-page__confirm p {
  margin: 0 0 var(--space-3);
  line-height: 1.7;
}

.judicial-page__confirm strong {
  color: var(--color-danger);
  font-weight: var(--font-weight-bold);
}

.judicial-page__confirm ul {
  list-style: none;
  margin: var(--space-3) 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.judicial-page__confirm ul li {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-soft);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text);
}

.judicial-page__confirm-q {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  font-size: var(--font-size-md);
  text-align: center;
  padding: var(--space-3) 0 0;
  border-top: 1px dashed var(--color-border);
}
</style>
