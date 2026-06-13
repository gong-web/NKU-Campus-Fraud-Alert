<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
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
  operator_id: undefined as string | undefined,
});
const page = ref<number>(1);
const size = ref<number>(20);
const data = ref<PaginationOut<AuditLogOut> | null>(null);
const loading = ref<boolean>(false);
const exporting = ref<boolean>(false);

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

const totalCount = computed<number>(() => data.value?.total ?? 0);
const totalPages = computed<number>(() => Math.max(1, Math.ceil(totalCount.value / size.value)));

async function exportCsv(): Promise<void> {
  exporting.value = true;
  try {
    await auditApi.exportCsv({
      ...(filters.op_type ? { op_type: filters.op_type } : {}),
      ...(filters.operator_id != null ? { operator_id: filters.operator_id } : {}),
      ...(filters.object_type ? { object_type: filters.object_type } : {}),
      ...(filters.object_id ? { object_id: filters.object_id } : {}),
    });
    ElMessage.success("审计日志 CSV 已导出");
  } catch {
    ElMessage.error("导出失败，请稍后重试");
  } finally {
    exporting.value = false;
  }
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
      badge="审计日志 · APPEND-ONLY"
      title="审计日志"
      subtitle="操作全留痕 · 任何角色不可删改 · 数据库 trigger 与 SDK 双重防护。"
    >
      <template #actions>
        <span
          v-if="data"
          class="audit-page__count-pill"
          aria-label="累计条数"
        >
          <AppIcon
            name="activity"
            :size="13"
          />
          累计 <strong>{{ totalCount.toLocaleString() }}</strong> 条
        </span>
        <AppButton
          variant="primary"
          :loading="exporting"
          @click="exportCsv"
        >
          <AppIcon
            name="download"
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
        <label class="audit-page__select-wrap">
          <span class="audit-page__select-label">操作类型</span>
          <select
            v-model="filters.op_type"
            class="audit-page__select"
            @change="page = 1; load()"
          >
            <option value="">全部</option>
            <option value="LOGIN">LOGIN · 登录</option>
            <option value="LOGIN_FAILED">LOGIN_FAILED · 登录失败</option>
            <option value="LOGOUT">LOGOUT · 登出</option>
            <option value="USER_CREATE">USER_CREATE · 创建账号</option>
            <option value="USER_DISABLE">USER_DISABLE · 停用账号</option>
            <option value="USER_ENABLE">USER_ENABLE · 启用账号</option>
            <option value="DECRYPT_ANONYMOUS">DECRYPT_ANONYMOUS · 司法解密</option>
          </select>
        </label>
        <label class="audit-page__select-wrap">
          <span class="audit-page__select-label">对象类型</span>
          <select
            v-model="filters.object_type"
            class="audit-page__select"
            @change="page = 1; load()"
          >
            <option value="">全部</option>
            <option value="user">user · 账号</option>
            <option value="report">report · 上报事件</option>
            <option value="audit_log">audit_log · 审计</option>
            <option value="judicial_request">judicial_request · 司法</option>
          </select>
        </label>
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
            <AppIcon
              name="filter"
              :size="13"
            />
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
        <AppStatusTag
          :status="opTone(row.operation_type)"
          :text="row.operation_type"
        />
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
            aria-label="第一页"
            @click="page = 1; load()"
          >«</button>
          <button
            type="button"
            class="audit-page__pager-btn"
            :disabled="page <= 1 || loading"
            aria-label="上一页"
            @click="page = page - 1; load()"
          >‹</button>
          <span class="audit-page__pager-num">
            {{ page }} / {{ totalPages }}
          </span>
          <button
            type="button"
            class="audit-page__pager-btn"
            :disabled="page >= totalPages || loading"
            aria-label="下一页"
            @click="page = page + 1; load()"
          >›</button>
          <button
            type="button"
            class="audit-page__pager-btn"
            :disabled="page >= totalPages || loading"
            aria-label="末页"
            @click="page = totalPages; load()"
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

.audit-page__count-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  background: var(--color-brand-50);
  border: 1px solid rgb(134 38 51 / 18%);
  color: var(--color-brand-700);
  font-size: var(--font-size-xs);
  letter-spacing: 0.04em;
  font-weight: var(--font-weight-medium);
}

.audit-page__count-pill strong {
  font-family: var(--font-family-mono);
  font-weight: var(--font-weight-bold);
  font-variant-numeric: tabular-nums;
  color: var(--color-text-strong);
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

.audit-page__select-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.audit-page__select-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
}

.audit-page__select {
  height: 38px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-family: inherit;
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  cursor: pointer;
  transition: all var(--duration-fast) var(--easing-out);
  appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, var(--color-text-tertiary) 50%),
    linear-gradient(135deg, var(--color-text-tertiary) 50%, transparent 50%);
  background-position: calc(100% - 14px) 50%, calc(100% - 9px) 50%;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  padding-right: 28px;
}

.audit-page__select:hover {
  border-color: var(--color-brand-400);
}

.audit-page__select:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
  border-color: var(--color-brand-500);
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
