<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { AppIcon, BrandLogo } from "@/components";

const router = useRouter();
const auth = useAuthStore();

const initial = computed<string>(() => {
  const name = auth.me?.real_name || "?";
  return Array.from(name)[0] ?? "?";
});

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const NAV: readonly NavItem[] = [
  { to: "/student/home", label: "首页", icon: "activity" },
];

async function handleLogout(): Promise<void> {
  const url = await auth.logout();
  if (url) window.location.href = url;
  else router.replace({ name: "login" });
}
</script>

<template>
  <div class="student-layout">
    <header class="student-layout__nav">
      <div class="student-layout__brand">
        <BrandLogo
          :size="30"
          variant="color"
        />
      </div>
      <nav
        v-if="NAV.length > 1"
        class="student-layout__menu"
      >
        <RouterLink
          v-for="item in NAV"
          :key="item.to"
          :to="item.to"
          class="student-layout__link"
        >
          <AppIcon
            :name="(item.icon as never)"
            :size="16"
          />
          {{ item.label }}
        </RouterLink>
      </nav>
      <span
        v-else
        class="student-layout__crumb"
      >
        <AppIcon
          name="graduation-cap"
          :size="13"
        />
        校园反诈
        <span class="student-layout__crumb-sep">·</span>
        <strong>学生工作台</strong>
      </span>
      <div class="student-layout__user">
        <span
          class="student-layout__avatar"
          aria-hidden="true"
        >
          {{ initial }}
          <span class="student-layout__avatar-dot" />
        </span>
        <div class="student-layout__user-meta">
          <strong>{{ auth.me?.real_name || "未登录" }}</strong>
          <small>学生 · 在校</small>
        </div>
        <button
          type="button"
          class="student-layout__logout"
          aria-label="退出登录"
          @click="handleLogout"
        >
          <AppIcon
            name="log-out"
            :size="14"
          />
          <span class="student-layout__logout-text">退出</span>
        </button>
      </div>
    </header>
    <main class="student-layout__content">
      <RouterView />
    </main>
    <footer class="student-layout__foot">
      <span>© 南开大学 · 校园电信诈骗上报与预警平台</span>
      <span class="student-layout__foot-divider">·</span>
      <span>反诈，是我们一起做的事</span>
    </footer>
  </div>
</template>

<style scoped>
.student-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.student-layout__nav {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-3) clamp(var(--space-4), 4vw, var(--space-7));
  background: var(--glass-surface-strong);
  backdrop-filter: blur(var(--glass-blur));
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-low);
}

.student-layout__brand {
  flex-shrink: 0;
}

.student-layout__menu {
  display: flex;
  gap: 4px;
}

.student-layout__crumb {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  background: linear-gradient(135deg, var(--color-brand-50) 0%, rgb(255 244 230 / 60%) 100%);
  border: 1px solid rgb(134 38 51 / 14%);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  letter-spacing: 0.06em;
  font-weight: var(--font-weight-medium);
}

.student-layout__crumb svg {
  color: var(--color-brand-600);
}

.student-layout__crumb-sep {
  color: var(--color-border-strong);
}

.student-layout__crumb strong {
  color: var(--color-brand-700);
  font-weight: var(--font-weight-semibold);
}

.student-layout__link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.02em;
  transition: all var(--duration-base) var(--easing-out);
}

.student-layout__link:hover {
  background: var(--color-brand-50);
  color: var(--color-brand-700);
}

.student-layout__link.router-link-active {
  background: var(--gradient-brand);
  color: #fff;
  box-shadow:
    var(--shadow-glow-brand),
    inset 0 1px 0 rgb(255 255 255 / 18%);
  text-shadow: 0 1px 2px rgb(31 8 11 / 32%);
}

.student-layout__link.router-link-active svg {
  color: var(--color-gold-200);
}

.student-layout__user {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.student-layout__avatar {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-family-serif);
  font-weight: var(--font-weight-bold);
  box-shadow:
    var(--shadow-glow-brand),
    inset 0 0 0 1px rgb(255 255 255 / 18%);
}

.student-layout__avatar-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow:
    0 0 0 2px var(--color-surface),
    0 0 8px rgb(46 125 50 / 60%);
}

.student-layout__user-meta {
  display: flex;
  flex-direction: column;
  font-size: 11px;
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
}

.student-layout__user-meta strong {
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  letter-spacing: 0;
}

.student-layout__logout {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 7px var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: inherit;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  transition: all var(--duration-base) var(--easing-out);
}

.student-layout__logout:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
  box-shadow: 0 0 0 3px rgb(198 40 40 / 10%);
}

.student-layout__content {
  flex: 1;
  padding: var(--space-6) clamp(var(--space-4), 4vw, var(--space-7));
  max-width: 1240px;
  margin: 0 auto;
  width: 100%;
}

.student-layout__foot {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
  font-size: 11px;
  color: var(--color-text-tertiary);
  letter-spacing: 0.06em;
}

.student-layout__foot-divider {
  color: var(--color-gold-300);
}

@media (width <= 640px) {
  .student-layout__nav {
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
  }

  .student-layout__crumb {
    display: none;
  }

  .student-layout__user-meta {
    display: none;
  }

  .student-layout__logout {
    padding: 6px;
    gap: 0;
  }

  .student-layout__logout-text {
    display: none;
  }

  .student-layout__foot {
    flex-wrap: wrap;
    gap: var(--space-2);
  }
}
</style>
