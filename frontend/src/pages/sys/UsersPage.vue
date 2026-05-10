<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import type { PaginationOut, UserOut } from "@/types/api";
import { usersApi } from "@/api/users";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppInput,
  AppModal,
  AppPageHeader,
  AppStatusTag,
  AppTable,
} from "@/components";

const filters = reactive({
  keyword: "",
  status: undefined as number | undefined,
});
const page = ref<number>(1);
const size = ref<number>(20);
const data = ref<PaginationOut<UserOut> | null>(null);
const loading = ref<boolean>(false);
const error = ref<string>("");

async function load(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const params: Parameters<typeof usersApi.list>[0] = {
      page: page.value,
      size: size.value,
    };
    if (filters.keyword) params.keyword = filters.keyword;
    if (filters.status != null) params.status = filters.status;
    data.value = await usersApi.list(params);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "加载失败";
    data.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(load);

const showCreate = ref<boolean>(false);
const newUser = reactive({
  cas_account: "",
  real_name: "",
  department_id: "1",
  role_id: "1",
});

async function submitCreate(): Promise<void> {
  await usersApi.create({
    cas_account: newUser.cas_account,
    real_name: newUser.real_name,
    department_id: Number(newUser.department_id) || 1,
    role_id: Number(newUser.role_id) || 1,
  });
  showCreate.value = false;
  newUser.cas_account = "";
  newUser.real_name = "";
  await load();
}

const columns = [
  { key: "cas_account" as const, title: "CAS 账号", width: "200px", mono: true },
  { key: "real_name" as const, title: "姓名", width: "150px" },
  { key: "department_id" as const, title: "院系" },
  { key: "role_id" as const, title: "角色", width: "150px" },
  { key: "status" as const, title: "状态", width: "120px" },
];

const DEPT_MAP: Record<number, string> = {
  1: "未指定",
  2: "计算机学院",
  3: "数学科学学院",
  4: "商学院",
  5: "外国语学院",
  6: "物理科学学院",
};

const ROLE_MAP: Record<number, string> = {
  1: "学生",
  2: "院系审核员",
  3: "校级审核员",
  4: "系统管理员",
};

const ROLE_TONE: Record<number, "info" | "warning" | "danger" | "success" | "neutral"> = {
  1: "info",
  2: "success",
  3: "warning",
  4: "danger",
};

function deptName(id: number): string {
  return DEPT_MAP[id] ?? `部门 ${id}`;
}

function roleName(id: number): string {
  return ROLE_MAP[id] ?? `角色 ${id}`;
}

function statusText(s: number): string {
  return ({ 1: "正常", 2: "已停用", 3: "已注销" } as const)[s as 1 | 2 | 3] ?? `未知(${s})`;
}

function avatarChar(name: string): string {
  const first = Array.from(name || "?")[0];
  return first ?? "?";
}

const stats = computed(() => {
  const items = data.value?.items ?? [];
  const total = data.value?.total ?? 0;
  const active = items.filter((u) => u.status === 1).length;
  return { total, active, disabled: items.length - active };
});
</script>

<template>
  <div class="users-page">
    <AppPageHeader
      badge="账号管理"
      title="账号管理"
      subtitle="账号创建 · 停用 · 角色变更 · 操作行为全部写入审计日志，不可绕过。"
    >
      <template #actions>
        <AppButton
          variant="primary"
          @click="showCreate = true"
        >
          <AppIcon
            name="user-cog"
            :size="14"
          />
          新建账号
        </AppButton>
      </template>
    </AppPageHeader>

    <p
      v-if="error"
      class="users-page__error"
    >
      <AppIcon
        name="alert-triangle"
        :size="14"
      />{{ error }}
    </p>

    <AppCard
      padding="md"
      class="users-page__filter"
    >
      <div class="users-page__filter-grid">
        <AppInput
          v-model="filters.keyword"
          placeholder="按姓名或 CAS 账号搜索"
          type="search"
          autocomplete="off"
        />
        <div class="users-page__filter-segment">
          <button
            type="button"
            class="users-page__filter-chip"
            :class="{ 'is-active': filters.status === undefined }"
            @click="filters.status = undefined; page = 1; load()"
          >全部</button>
          <button
            type="button"
            class="users-page__filter-chip"
            :class="{ 'is-active': filters.status === 1 }"
            @click="filters.status = 1; page = 1; load()"
          >正常</button>
          <button
            type="button"
            class="users-page__filter-chip"
            :class="{ 'is-active': filters.status === 2 }"
            @click="filters.status = 2; page = 1; load()"
          >已停用</button>
        </div>
        <span class="users-page__filter-stat">
          <span>共 <strong>{{ stats.total }}</strong> 个账号</span>
          <span class="dot" />
          <span>本页活跃 <strong>{{ stats.active }}</strong></span>
        </span>
        <div class="users-page__filter-actions">
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
        </div>
      </div>
    </AppCard>

    <AppTable
      :rows="data?.items ?? []"
      :columns="columns"
      :loading="loading"
      :zebra="false"
      row-key="user_id"
      empty-title="暂无账号"
      empty-hint="点击右上角「新建账号」创建第一个账号"
    >
      <template #cell-cas_account="{ row }">
        <div class="users-page__cas">
          <span class="users-page__avatar">{{ avatarChar(String(row.real_name)) }}</span>
          <span class="users-page__cas-id">{{ row.cas_account }}</span>
        </div>
      </template>
      <template #cell-real_name="{ row }">
        <strong class="users-page__name">{{ row.real_name }}</strong>
      </template>
      <template #cell-department_id="{ row }">
        <span class="users-page__dept">
          <AppIcon
            name="info"
            :size="12"
          />
          {{ deptName(Number(row.department_id)) }}
        </span>
      </template>
      <template #cell-role_id="{ row }">
        <AppStatusTag
          :status="ROLE_TONE[Number(row.role_id)] ?? 'neutral'"
          :text="roleName(Number(row.role_id))"
        />
      </template>
      <template #cell-status="{ row }">
        <AppStatusTag
          :status="row.status === 1 ? 'success' : row.status === 2 ? 'danger' : 'neutral'"
          :text="statusText(Number(row.status))"
        />
      </template>
      <template #footer>
        <span
          v-if="data"
          class="users-page__footer-meta"
        >
          第 <strong>{{ data.page }}</strong> 页 · 共
          <strong>{{ data.total }}</strong> 条 · 每页 {{ size }}
        </span>
        <span
          v-if="data"
          class="users-page__pager"
        >
          <button
            type="button"
            class="users-page__pager-btn"
            :disabled="page <= 1 || loading"
            @click="page = page - 1; load()"
            aria-label="上一页"
          >‹ 上一页</button>
          <button
            type="button"
            class="users-page__pager-btn"
            :disabled="page * size >= data.total || loading"
            @click="page = page + 1; load()"
            aria-label="下一页"
          >下一页 ›</button>
        </span>
        <span class="users-page__footer-hint">
          <AppIcon
            name="shield-check"
            :size="12"
          />
          所有变更已写入审计
        </span>
      </template>
    </AppTable>

    <AppModal
      v-model="showCreate"
      title="新建账号"
      width="520px"
    >
      <p class="users-page__form-hint">
        新建账号后将通过站内信通知本人，初始状态为「正常」。请仔细核对信息，
        <strong>此操作会写入审计日志</strong>。
      </p>
      <div class="form-grid">
        <AppInput
          v-model="newUser.cas_account"
          label="CAS 账号"
          :required="true"
          placeholder="如 student123"
        />
        <AppInput
          v-model="newUser.real_name"
          label="姓名"
          :required="true"
          placeholder="真实姓名"
        />
        <AppInput
          v-model="newUser.department_id"
          label="院系 ID"
          type="text"
          hint="1=未指定 · 2=计院 · 3=数院 · 4=商院"
        />
        <AppInput
          v-model="newUser.role_id"
          label="角色 ID"
          type="text"
          hint="1=学生 · 2=院系审 · 3=校级审 · 4=系统管理员"
        />
      </div>
      <template #footer>
        <AppButton
          variant="secondary"
          @click="showCreate = false"
        >
          取消
        </AppButton>
        <AppButton
          variant="primary"
          @click="submitCreate"
        >
          <AppIcon
            name="user-cog"
            :size="14"
          />
          确认创建
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.users-page__error {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(198 40 40 / 6%);
  border: 1px solid rgb(198 40 40 / 22%);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.users-page__filter-grid {
  display: grid;
  grid-template-columns: 1.5fr auto auto auto;
  gap: var(--space-4);
  align-items: center;
}

@media (width <= 1024px) {
  .users-page__filter-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (width <= 640px) {
  .users-page__filter-grid {
    grid-template-columns: 1fr;
  }
}

.users-page__filter-segment {
  display: inline-flex;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 3px;
  gap: 2px;
}

.users-page__filter-chip {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  border: 0;
  background: transparent;
  font-family: inherit;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.04em;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--easing-out);
  white-space: nowrap;
}

.users-page__filter-chip:hover:not(.is-active) {
  color: var(--color-brand-700);
  background: var(--color-brand-50);
}

.users-page__filter-chip.is-active {
  background: var(--color-surface);
  color: var(--color-brand-700);
  font-weight: var(--font-weight-semibold);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    0 1px 3px rgb(15 18 28 / 8%),
    0 0 0 1px rgb(134 38 51 / 18%);
}

.users-page__filter-stat {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  letter-spacing: 0.02em;
}

.users-page__filter-stat strong {
  color: var(--color-text-strong);
  font-family: var(--font-family-mono);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-sm);
}

.users-page__filter-stat .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-gold-400);
}

.users-page__filter-actions {
  display: flex;
  gap: var(--space-2);
}

.users-page__cas {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}

.users-page__avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-family-serif);
  font-weight: var(--font-weight-bold);
  font-size: 13px;
  box-shadow:
    0 2px 6px rgb(134 38 51 / 32%),
    inset 0 0 0 1px rgb(255 255 255 / 18%);
  flex-shrink: 0;
}

.users-page__cas-id {
  font-family: var(--font-family-mono);
  letter-spacing: 0.02em;
  color: var(--color-text-strong);
}

.users-page__name {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.users-page__dept {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-secondary);
}

.users-page__footer-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-success);
  font-size: 11px;
}

.users-page__footer-meta strong {
  font-family: var(--font-family-mono);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-bold);
  font-variant-numeric: tabular-nums;
}

.users-page__pager {
  display: inline-flex;
  gap: 4px;
  margin: 0 auto;
}

.users-page__pager-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-family: inherit;
  font-size: 11.5px;
  letter-spacing: 0.02em;
  font-weight: var(--font-weight-medium);
  transition: all var(--duration-fast) var(--easing-out);
}

.users-page__pager-btn:hover:not(:disabled) {
  border-color: var(--color-brand-400);
  color: var(--color-brand-700);
  background: var(--color-brand-50);
}

.users-page__pager-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.users-page__form-hint {
  margin: 0 0 var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(239 108 0 / 6%);
  border: 1px solid rgb(239 108 0 / 22%);
  color: var(--color-text);
  font-size: var(--font-size-xs);
  line-height: 1.6;
}

.users-page__form-hint strong {
  color: var(--color-warning);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3) var(--space-4);
}

@media (width <= 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
