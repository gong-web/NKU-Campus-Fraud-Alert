<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/stores/auth";
import { roleHome } from "@/router";
import AuthLayout from "@/layouts/AuthLayout.vue";
import { AppButton, AppIcon } from "@/components";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const provider = ref<string>("");
const healthy = ref<boolean>(true);
const loading = ref<boolean>(false);
const message = ref<string>("");

const isMock = import.meta.env.VITE_AUTH_PROVIDER === "mock";
const providerName = computed<string>(() => {
  if (provider.value === "mock") return "Mock CAS（开发）";
  if (provider.value === "real") return "南开大学统一身份认证";
  return provider.value || "未知";
});

onMounted(async () => {
  if (route.query.reason === "forbidden") {
    message.value = "你没有访问该页面的权限。请使用相应角色的账号登录。";
  }
  if (route.query.reason === "expired") {
    message.value = "会话已过期，请重新登录。";
  }
  if (auth.isLoggedIn) {
    void router.replace(roleHome(auth.role));
    return;
  }
  try {
    const r = await authApi.loginUrl();
    provider.value = r.provider;
    healthy.value = r.healthy;
  } catch {
    healthy.value = false;
  }
});

async function handleCasLogin(): Promise<void> {
  loading.value = true;
  try {
    const r = await authApi.loginUrl();
    window.location.href = r.login_url;
  } finally {
    loading.value = false;
  }
}

function handleMockLogin(): void {
  void router.push({ name: "mock-login" });
}
</script>

<template>
  <AuthLayout
    subtitle="请使用学校统一身份认证账号登录平台。我们不存储你的密码。"
  >
    <template #title>
      <h1 class="login__title">
        <span>欢迎登录</span>
        <small>校园电信诈骗上报与预警平台</small>
      </h1>
    </template>

    <div
      class="login__provider"
      :class="{ 'is-down': !healthy }"
    >
      <span class="login__provider-dot" />
      <div>
        <strong>{{ providerName }}</strong>
        <p>
          <template v-if="healthy">
            统一身份认证服务运行正常，可正常登录。
          </template>
          <template v-else>
            统一身份认证服务暂时不可用，请稍后再试。
          </template>
        </p>
      </div>
      <span class="login__provider-pill">
        {{ healthy ? 'ONLINE' : 'OFFLINE' }}
      </span>
    </div>

    <p
      v-if="message"
      class="login__error"
      role="alert"
    >
      <span class="login__error-icon">
        <AppIcon
          name="alert-triangle"
          :size="14"
        />
      </span>
      {{ message }}
    </p>

    <AppButton
      variant="primary"
      size="lg"
      :block="true"
      :loading="loading"
      :disabled="!healthy"
      @click="handleCasLogin"
    >
      <AppIcon
        name="log-in"
        :size="18"
      />
      使用学校 CAS 登录
    </AppButton>

    <div class="login__divider">
      <span>仅开发环境</span>
    </div>

    <AppButton
      variant="secondary"
      :block="true"
      :disabled="!isMock"
      @click="handleMockLogin"
    >
      <AppIcon
        name="key"
        :size="16"
      />
      <template v-if="isMock">
        Mock 登录（输入学号即可）
      </template>
      <template v-else>
        Mock 登录已禁用
      </template>
    </AppButton>

    <div class="login__notes">
      <div class="login__note">
        <span class="login__note-icon login__note-icon--ok">
          <AppIcon
            name="shield-check"
            :size="14"
          />
        </span>
        <span>所有登录会话经 HttpOnly Cookie 管理；CSRF / 重放双重防护。</span>
      </div>
      <div class="login__note">
        <span class="login__note-icon">
          <AppIcon
            name="info"
            :size="14"
          />
        </span>
        <span>
          登录遇到困难？联系信息化办（<a href="mailto:helpdesk@nankai.edu.cn">helpdesk@nankai.edu.cn</a>）。
        </span>
      </div>
    </div>
  </AuthLayout>
</template>

<style scoped>
.login__title {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.025em;
  color: var(--color-text-strong);
}

.login__title small {
  font-family: var(--font-family-sans);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-regular);
  color: var(--color-text-secondary);
  letter-spacing: 0;
}

.login__provider {
  display: grid;
  grid-template-columns: 12px 1fr auto;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background:
    linear-gradient(180deg, rgb(46 125 50 / 6%), rgb(46 125 50 / 2%));
  border: 1px solid rgb(46 125 50 / 22%);
  margin-bottom: var(--space-3);
}

.login__provider strong {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: 0.01em;
}

.login__provider p {
  margin: 2px 0 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.login__provider-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-success);
  margin-top: 2px;
  box-shadow:
    0 0 0 4px rgb(46 125 50 / 16%),
    0 0 8px rgb(46 125 50 / 32%);
  animation: login-pulse 1.8s ease-out infinite;
}

.login__provider-pill {
  font-family: var(--font-family-mono);
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.18em;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  background: rgb(46 125 50 / 12%);
  color: var(--color-success);
  border: 1px solid rgb(46 125 50 / 32%);
}

.login__provider.is-down {
  background:
    linear-gradient(180deg, rgb(198 40 40 / 6%), rgb(198 40 40 / 2%));
  border-color: rgb(198 40 40 / 22%);
}

.login__provider.is-down .login__provider-dot {
  background: var(--color-danger);
  box-shadow:
    0 0 0 4px rgb(198 40 40 / 14%),
    0 0 8px rgb(198 40 40 / 32%);
}

.login__provider.is-down .login__provider-pill {
  background: rgb(198 40 40 / 12%);
  color: var(--color-danger);
  border-color: rgb(198 40 40 / 32%);
}

@keyframes login-pulse {
  0% {
    box-shadow:
      0 0 0 0 rgb(46 125 50 / 36%),
      0 0 8px rgb(46 125 50 / 32%);
  }

  100% {
    box-shadow:
      0 0 0 12px rgb(46 125 50 / 0%),
      0 0 8px rgb(46 125 50 / 32%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .login__provider-dot { animation: none; }
}

.login__error {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: var(--space-2);
  align-items: center;
  margin: 0 0 var(--space-2);
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  border-radius: var(--radius-md);
  color: var(--color-danger);
  background: rgb(198 40 40 / 6%);
  border: 1px solid rgb(198 40 40 / 22%);
  border-left: 3px solid var(--color-danger);
}

.login__error-icon {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: rgb(198 40 40 / 14%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.login__divider {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-weight: var(--font-weight-semibold);
  margin: var(--space-3) 0;
}

.login__divider::before,
.login__divider::after {
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

.login__notes {
  margin-top: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--color-border);
}

.login__note {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: var(--space-2);
  align-items: center;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.login__note-icon {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--color-neutral-100);
  color: var(--color-text-tertiary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.login__note-icon--ok {
  background: rgb(46 125 50 / 10%);
  color: var(--color-success);
}

.login__note a {
  color: var(--color-brand-700);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}

.login__note a:hover {
  color: var(--color-brand-800);
}
</style>
