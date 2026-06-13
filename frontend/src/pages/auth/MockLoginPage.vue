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
    role: "系统管理员",
    icon: "user-cog",
    tone: "brand",
  },
  {
    id: "review-school",
    account: "reviewer_school001",
    display: "校级审核员",
    role: "校级审核员",
    icon: "scale",
    tone: "info",
  },
  {
    id: "review-dept",
    account: "reviewer_dept001",
    display: "院系审核员",
    role: "院系审核员 · 计算机学院",
    icon: "users",
    tone: "info",
  },
  {
    id: "student",
    account: "student001",
    display: "学生 · 张三",
    role: "学生 · 计算机学院",
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
  <AuthLayout subtitle="选择下方账号，或手动输入学号/工号登录。">
    <template #title>
      <h1 class="mock-login__title">
        <span>快捷登录</span>
      </h1>
    </template>

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
        label="学号/工号"
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

    <p class="mock-login__back">
      <RouterLink :to="{ name: 'login' }">
        返回统一认证登录
      </RouterLink>
    </p>
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

.mock-login__back {
  margin: var(--space-4) 0 0;
  text-align: center;
  font-size: var(--font-size-sm);
}

.mock-login__back a {
  color: var(--color-text-secondary);
  text-decoration: none;
}

.mock-login__back a:hover {
  color: var(--color-brand-700);
  text-decoration: underline;
}
</style>
