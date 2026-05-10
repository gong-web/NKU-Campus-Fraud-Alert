<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { roleHome } from "@/router";
import AuthLayout from "@/layouts/AuthLayout.vue";
import { AppButton, AppIcon, AppInput } from "@/components";

const router = useRouter();
const auth = useAuthStore();

interface RolePreset {
  id: "sys" | "review-school" | "review-dept" | "student";
  account: string;
  display: string;
  role: string;
  icon: string;
  tone: "brand" | "info" | "success" | "neutral";
}

const PRESETS: readonly RolePreset[] = [
  {
    id: "sys",
    account: "sysadmin001",
    display: "系统管理员",
    role: "SYS_ADMIN · 全部权限",
    icon: "user-cog",
    tone: "brand",
  },
  {
    id: "review-school",
    account: "reviewer_school001",
    display: "校级审核员",
    role: "REVIEWER · 校级",
    icon: "scale",
    tone: "info",
  },
  {
    id: "review-dept",
    account: "reviewer_dept001",
    display: "院系审核员",
    role: "REVIEWER · 计算机学院",
    icon: "users",
    tone: "info",
  },
  {
    id: "student",
    account: "student001",
    display: "学生 · 张三",
    role: "STUDENT · 计算机学院",
    icon: "graduation-cap",
    tone: "success",
  },
];

const casAccount = ref<string>("");
const submitting = ref<boolean>(false);
const error = ref<string>("");
const activePreset = ref<RolePreset["id"] | null>(null);

async function loginAs(preset: RolePreset): Promise<void> {
  activePreset.value = preset.id;
  casAccount.value = preset.account;
  await submit();
}

async function submit(): Promise<void> {
  if (!casAccount.value.trim()) {
    error.value = "请输入学号或工号，或点击右侧的角色快捷登录。";
    return;
  }
  submitting.value = true;
  error.value = "";
  try {
    const me = await auth.mockLogin(casAccount.value.trim());
    void router.replace(roleHome(me.role_code));
  } catch (e) {
    error.value = e instanceof Error ? e.message : "登录失败，请稍后重试。";
  } finally {
    submitting.value = false;
    activePreset.value = null;
  }
}
</script>

<template>
  <AuthLayout
    eyebrow="DEV · MOCK LOGIN"
    subtitle="无需密码，仅在 AUTH_PROVIDER=mock 时可用，便于 4 位组员开发联调。"
  >
    <template #title>
      <h1 class="mock-login__title">
        <span>角色快捷登录</span>
        <small>选择一个种子账号 1 秒进入对应工作台</small>
      </h1>
    </template>

    <div class="mock-login__hint-top">
      <AppIcon
        name="info"
        :size="14"
      />
      <span>4 个种子账号已预置，覆盖系统管理员、校级审核员、院系审核员、学生。</span>
    </div>

    <ul class="mock-login__roles">
      <li
        v-for="(preset, i) in PRESETS"
        :key="preset.id"
        :style="{ animationDelay: `${0.06 * i}s` }"
      >
        <button
          type="button"
          class="mock-login__role"
          :class="`mock-login__role--${preset.tone}`"
          :disabled="submitting"
          :data-loading="activePreset === preset.id || undefined"
          @click="loginAs(preset)"
        >
          <span class="mock-login__role-icon">
            <AppIcon
              :name="(preset.icon as never)"
              :size="20"
            />
          </span>
          <span class="mock-login__role-text">
            <strong>{{ preset.display }}</strong>
            <small>{{ preset.role }}</small>
          </span>
          <code>{{ preset.account }}</code>
          <AppIcon
            name="arrow-right"
            :size="16"
            class="mock-login__role-arrow"
          />
        </button>
      </li>
    </ul>

    <div class="mock-login__divider">
      <span>或手动输入</span>
    </div>

    <form
      class="mock-login__form"
      @submit.prevent="submit"
    >
      <AppInput
        v-model="casAccount"
        label="CAS 账号"
        placeholder="如 student001 / sysadmin001"
        :required="true"
        :error="error"
        autocomplete="off"
      />
      <AppButton
        type="submit"
        variant="primary"
        size="lg"
        :block="true"
        :loading="submitting && activePreset === null"
      >
        <AppIcon
          name="log-in"
          :size="18"
        />
        登录
      </AppButton>
    </form>

    <div class="mock-login__hint">
      <span class="mock-login__hint-icon">
        <AppIcon
          name="shield-alert"
          :size="14"
        />
      </span>
      <span>
        <strong>仅开发环境</strong> · 生产配置 <code>AUTH_PROVIDER=real</code> 时此入口被后端直接禁用。
        请勿提交真实账号到日志。
      </span>
    </div>
  </AuthLayout>
</template>

<style scoped>
.mock-login__title {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.02em;
  color: var(--color-text-strong);
}

.mock-login__title small {
  font-family: var(--font-family-sans);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-regular);
  color: var(--color-text-secondary);
  letter-spacing: 0;
}

.mock-login__hint-top {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  margin-bottom: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-brand-50);
  border: 1px solid rgb(134 38 51 / 14%);
  border-left: 3px solid var(--color-brand-500);
  color: var(--color-brand-700);
  font-size: var(--font-size-xs);
  line-height: 1.5;
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.01em;
}

.mock-login__roles {
  list-style: none;
  margin: 0 0 var(--space-3);
  padding: 0;
  display: grid;
  gap: var(--space-2);
}

.mock-login__roles > li {
  animation: mock-role-in 500ms var(--easing-out) both;
}

@keyframes mock-role-in {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.mock-login__role {
  width: 100%;
  display: grid;
  grid-template-columns: 40px 1fr auto auto;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  cursor: pointer;
  text-align: left;
  font: inherit;
  color: inherit;
  position: relative;
  overflow: hidden;
  transition:
    border-color var(--duration-base) var(--easing-out),
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    background var(--duration-base) var(--easing-out);
}

.mock-login__role::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: transparent;
  transition: background var(--duration-base) var(--easing-out);
}

.mock-login__role--brand:hover::before { background: var(--color-brand-500); }
.mock-login__role--info:hover::before { background: var(--color-info); }
.mock-login__role--success:hover::before { background: var(--color-success); }

.mock-login__role:disabled {
  opacity: 0.55;
  cursor: progress;
}

.mock-login__role:hover:not(:disabled) {
  border-color: var(--color-brand-300);
  transform: translateX(2px);
  box-shadow: var(--shadow-low);
  background: var(--color-bg-soft);
}

.mock-login__role[data-loading] {
  border-color: var(--color-brand-500);
  box-shadow: var(--shadow-ring-brand);
}

.mock-login__role[data-loading]::before {
  background: var(--color-brand-500);
}

.mock-login__role-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
}

.mock-login__role--brand .mock-login__role-icon {
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  border-color: rgb(134 38 51 / 14%);
}

.mock-login__role--info .mock-login__role-icon {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
  border-color: rgb(21 101 192 / 18%);
}

.mock-login__role--success .mock-login__role-icon {
  background: rgb(46 125 50 / 10%);
  color: var(--color-success);
  border-color: rgb(46 125 50 / 18%);
}

.mock-login__role--neutral .mock-login__role-icon {
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
}

.mock-login__role-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mock-login__role-text strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.mock-login__role-text small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 1px;
}

.mock-login__role code {
  font-family: var(--font-family-mono);
  font-size: 10.5px;
  font-weight: var(--font-weight-medium);
  background: var(--color-neutral-50);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  letter-spacing: 0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
  font-variant-numeric: tabular-nums;
}

.mock-login__role:hover:not(:disabled) code {
  background: var(--color-brand-50);
  border-color: rgb(134 38 51 / 22%);
  color: var(--color-brand-700);
}

@media (width <= 640px) {
  .mock-login__role code {
    display: none;
  }

  .mock-login__role {
    grid-template-columns: 40px 1fr auto;
  }
}

.mock-login__role-arrow {
  color: var(--color-text-tertiary);
  transition: transform var(--duration-base) var(--easing-out);
}

.mock-login__role:hover:not(:disabled) .mock-login__role-arrow {
  transform: translateX(2px);
  color: var(--color-brand-600);
}

.mock-login__divider {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: 10.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: var(--font-weight-semibold);
  margin: var(--space-2) 0 var(--space-3);
  opacity: 0.7;
}

.mock-login__divider::before,
.mock-login__divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    var(--color-border) 50%,
    transparent
  );
}

.mock-login__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.mock-login__hint {
  margin-top: var(--space-4);
  padding: 10px var(--space-3);
  border-radius: var(--radius-md);
  background: rgb(239 108 0 / 6%);
  border: 1px solid rgb(239 108 0 / 22%);
  border-left: 3px solid var(--color-warning);
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: var(--space-2);
  align-items: center;
}

.mock-login__hint-icon {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: rgb(239 108 0 / 14%);
  color: var(--color-warning);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.mock-login__hint span:last-child {
  font-size: var(--font-size-xs);
  color: var(--color-text);
  line-height: 1.65;
}

.mock-login__hint strong {
  color: var(--color-warning);
  font-weight: var(--font-weight-bold);
}

.mock-login__hint code {
  font-family: var(--font-family-mono);
  font-size: 11px;
  padding: 1px 5px;
  background: var(--color-neutral-100);
  border-radius: 3px;
  color: var(--color-text);
}
</style>
