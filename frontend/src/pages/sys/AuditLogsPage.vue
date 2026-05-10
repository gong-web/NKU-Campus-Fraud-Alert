<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import type { AuditLogOut, PaginationOut } from "@/types/api";
import { auditApi } from "@/api/audit";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppInput,
  AppPageHeader,
  AppStatusTag,
  AppTable,
} from "@/components";

const filters = reactive({
  op_type: "",
  object_type: "",
  object_id: "",
  operator_id: undefined as number | undefined,
});
const page = ref<number>(1);
const size = ref<number>(20);
const data = ref<PaginationOut<AuditLogOut> | null>(null);
const loading = ref<boolean>(false);

async function load(): Promise<void> {
  loading.value = true;
  try {
    const params: Parameters<typeof auditApi.list>[0] = {
      page: page.value,
      size: size.value,
    };
    if (filters.op_type) params.op_type = filters.op_type;
    if (filters.object_type) params.object_type = filters.object_type;
    if (filters.object_id) params.object_id = filters.object_id;
    if (filters.operator_id != null) params.operator_id = filters.operator_id;
    data.value = await auditApi.list(params);
  } finally {
    loading.value = false;
  }
}

function reset(): void {
  filters.op_type = "";
  filters.object_type = "";
  filters.object_id = "";
  filters.operator_id = undefined;
  page.value = 1;
  void load();
}

onMounted(load);

const columns = [
  { key: "operated_at" as const, title: "时间", width: "118px", mono: true },
  { key: "operation_type" as const, title: "操作", width: "172px" },
  { key: "operator_id" as const, title: "操作人", width: "168px", mono: true },
  { key: "object_type" as const, title: "对象", width: "84px" },
  { key: "object_id" as const, title: "对象 ID", width: "150px", mono: true },
  { key: "source_ip" as const, title: "来源 IP", width: "140px", mono: true },
  { key: "trace_id" as const, title: "Trace ID", mono: true },
];

function fmtTime(iso: string | undefined): { date: string; time: string } {
  if (!iso) return { date: "—", time: "" };
  const d = new Date(iso);
  const date = `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`;
  const time = d.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
  return { date, time };
}

function opTone(op: string): "info" | "success" | "warning" | "danger" | "neutral" {
  if (op === "LOGIN_FAILED") return "warning";
  if (op.startsWith("DECRYPT")) return "danger";
  if (op.startsWith("USER")) return "info";
  if (op === "LOGIN") return "success";
  return "neutral";
}

function opIcon(op: string): string {
  if (op.startsWith("LOGIN")) return "log-in";
  if (op === "LOGOUT") return "log-out";
  if (op.startsWith("USER")) return "user-cog";
  if (op.startsWith("DECRYPT")) return "scale";
  return "activity";
}

const totalCount = computed<number>(() => data.value?.total ?? 0);
const totalPages = computed<number>(() => Math.max(1, Math.ceil(totalCount.value / size.value)));

function exportCsv(): void {
  const url = new URL("/api/v1/audit-logs/export", window.location.origin);
  if (filters.op_type) url.searchParams.set("op_type", filters.op_type);
  if (filters.operator_id != null) url.searchParams.set("operator_id", String(filters.operator_id));
  window.location.href = url.toString();
}

function shortTrace(t: string | null | undefined): string {
  if (!t) return "—";
  if (t.length <= 16) return t;
  return `${t.slice(0, 8)}…${t.slice(-6)}`;
}

function shortId(v: unknown): string {
  const s = String(v ?? "");
  if (s.length <= 10) return s;
  return `${s.slice(0, 4)}…${s.slice(-4)}`;
}
</script>

<template>
  <div class="audit-page">
    <AppPageHeader
      badge="审计日志"
      title="审计日志"
      subtitle="操作全留痕 · 任何角色不可删改 · 数据库 trigger 与 SDK 双重防护。"
    >
      <template #actions>
        <AppButton
          variant="secondary"
          @click="exportCsv"
        >
          <AppIcon
            name="arrow-right"
            :size="14"
          />
          导出 CSV
        </AppButton>
      </template>
    </AppPageHeader>

    <AppCard
      padding="md"
      class="audit-page__filter"
    >
      <div class="audit-page__filter-grid">
        <AppInput
          v-model="filters.op_type"
          label="操作类型"
          placeholder="如 LOGIN / DECRYPT_ANONYMOUS"
        />
        <AppInput
          v-model="filters.object_type"
          label="对象类型"
          placeholder="如 user / report"
        />
        <AppInput
          v-model="filters.object_id"
          label="对象 ID"
          placeholder="精确匹配"
        />
        <div class="audit-page__filter-actions">
          <AppButton
            variant="primary"
            @click="page = 1; load()"
          >
            <AppIcon
              name="activity"
              :size="14"
            />
            查询
          </AppButton>
          <AppButton
            variant="ghost"
            @click="reset"
          >
            重置
          </AppButton>
        </div>
      </div>
    </AppCard>

    <AppTable
      :rows="data?.items ?? []"
      :columns="columns"
      :loading="loading"
      :zebra="true"
      row-key="log_id"
      empty-title="暂无审计日志"
      empty-hint="系统操作后将自动记录"
    >
      <template #cell-operated_at="{ row }">
        <div class="audit-page__time">
          <strong>{{ fmtTime(row.operated_at).date }}</strong>
          <small>{{ fmtTime(row.operated_at).time }}</small>
        </div>
      </template>
      <template #cell-operation_type="{ row }">
        <span class="audit-page__op">
          <span
            class="audit-page__op-icon"
            :class="`audit-page__op-icon--${opTone(row.operation_type)}`"
          >
            <AppIcon
              :name="(opIcon(row.operation_type) as never)"
              :size="13"
            />
          </span>
          <AppStatusTag
            :status="opTone(row.operation_type)"
            :text="row.operation_type"
          />
        </span>
      </template>
      <template #cell-operator_id="{ row }">
        <span
          class="audit-page__id"
          :title="String(row.operator_id)"
        >#{{ shortId(row.operator_id) }}</span>
      </template>
      <template #cell-object_id="{ row }">
        <span
          class="audit-page__objid"
          :title="String(row.object_id || '')"
        >{{ row.object_id ? shortId(row.object_id) : '—' }}</span>
      </template>
      <template #cell-source_ip="{ row }">
        <span class="audit-page__ip">{{ row.source_ip || "—" }}</span>
      </template>
      <template #cell-trace_id="{ row }">
        <span
          class="audit-page__trace"
          :title="row.trace_id || ''"
        >
          {{ shortTrace(row.trace_id) }}
        </span>
      </template>
      <template #footer>
        <span
          v-if="data"
          class="audit-page__footer-meta"
        >
          共 <strong>{{ totalCount.toLocaleString() }}</strong> 条 · 当前第
          <strong>{{ page }}</strong> / {{ totalPages }} 页 · 每页 {{ size }}
        </span>
        <span class="audit-page__pager">
          <button
            type="button"
            class="audit-page__pager-btn"
            :disabled="page <= 1 || loading"
            @click="page = 1; load()"
            aria-label="第一页"
          >«</button>
          <button
            type="button"
            class="audit-page__pager-btn"
            :disabled="page <= 1 || loading"
            @click="page = page - 1; load()"
            aria-label="上一页"
          >‹</button>
          <span class="audit-page__pager-num">
            {{ page }} / {{ totalPages }}
          </span>
          <button
            type="button"
            class="audit-page__pager-btn"
            :disabled="page >= totalPages || loading"
            @click="page = page + 1; load()"
            aria-label="下一页"
          >›</button>
          <button
            type="button"
            class="audit-page__pager-btn"
            :disabled="page >= totalPages || loading"
            @click="page = totalPages; load()"
            aria-label="末页"
          >»</button>
        </span>
        <span class="audit-page__footer-hint">
          <AppIcon
            name="shield-check"
            :size="12"
          />
          仅展示，不可删改
        </span>
      </template>
    </AppTable>
  </div>
</template>

<style scoped>
.audit-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.audit-page__filter {
  position: sticky;
  top: var(--space-3);
  z-index: 5;
  backdrop-filter: blur(8px);
}

.audit-page__filter-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr auto;
  gap: var(--space-3);
  align-items: end;
}

@media (width <= 1024px) {
  .audit-page__filter-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (width <= 640px) {
  .audit-page__filter-grid {
    grid-template-columns: 1fr;
  }
}

.audit-page__filter-actions {
  display: flex;
  gap: var(--space-2);
}

.audit-page__time {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  font-family: var(--font-family-mono);
}

.audit-page__time strong {
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.audit-page__time small {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.audit-page__op {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.audit-page__op-icon {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.audit-page__op-icon--success {
  background: rgb(46 125 50 / 12%);
  color: var(--color-success);
}

.audit-page__op-icon--info {
  background: rgb(21 101 192 / 12%);
  color: var(--color-info);
}

.audit-page__op-icon--warning {
  background: rgb(239 108 0 / 14%);
  color: var(--color-warning);
}

.audit-page__op-icon--danger {
  background: rgb(198 40 40 / 12%);
  color: var(--color-danger);
}

.audit-page__op-icon--neutral {
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
}

.audit-page__id {
  display: inline-block;
  color: var(--color-brand-700);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  word-break: keep-all;
}

.audit-page__ip {
  color: var(--color-text);
  background: var(--color-bg);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  font-size: 12px;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.audit-page__objid {
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-text-secondary);
  letter-spacing: 0.02em;
  cursor: help;
}

.audit-page__trace {
  color: var(--color-text-tertiary);
  font-size: 11.5px;
  letter-spacing: 0.04em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 220px;
}

.audit-page__footer-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-success);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.audit-page__footer-meta strong {
  font-family: var(--font-family-mono);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-bold);
  font-variant-numeric: tabular-nums;
}

.audit-page__pager {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 2px;
  box-shadow: var(--shadow-low);
  margin: 0 auto;
}

.audit-page__pager-btn {
  width: 28px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-family: var(--font-family-serif);
  font-size: 14px;
  font-weight: var(--font-weight-bold);
  line-height: 1;
  transition: all var(--duration-fast) var(--easing-out);
}

.audit-page__pager-btn:hover:not(:disabled) {
  background: var(--color-brand-50);
  color: var(--color-brand-700);
}

.audit-page__pager-btn:disabled {
  opacity: 0.32;
  cursor: not-allowed;
}

.audit-page__pager-num {
  font-family: var(--font-family-mono);
  font-size: 11.5px;
  letter-spacing: 0.04em;
  padding: 0 8px;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}
</style>
