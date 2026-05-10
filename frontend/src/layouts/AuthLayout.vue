<script setup lang="ts">
import { BrandLogo, HeroIllustration, AppIcon } from "@/components";

defineProps<{ subtitle?: string; eyebrow?: string }>();

const features: { icon: string; title: string; desc: string }[] = [
  {
    icon: "shield-check",
    title: "学校 CAS 单点登录",
    desc: "复用统一身份认证，零额外密码、零信任飞地。",
  },
  {
    icon: "lock",
    title: "证据加密 · 匿名隔离",
    desc: "AES-256-GCM 落库；匿名上报由独立账号管理。",
  },
  {
    icon: "scale",
    title: "审计日志不可改",
    desc: "数据库 trigger 强制 append-only，操作全留痕。",
  },
];
</script>

<template>
  <main class="auth-layout">
    <!-- 左侧品牌 / 叙事栏 -->
    <section
      class="auth-layout__art"
      aria-hidden="true"
    >
      <div class="auth-layout__art-grid" />
      <div class="auth-layout__art-noise" />

      <!-- 校训书法水印（中文衬线放大字号、超低透明度） -->
      <div class="auth-layout__art-motto">
        允公允能 · 日新月异
      </div>

      <!-- 落款印章 -->
      <div class="auth-layout__art-seal">
        <span>南</span>
        <span>开</span>
      </div>

      <div class="auth-layout__art-content">
        <BrandLogo
          :size="42"
          variant="white"
        />

        <div class="auth-layout__art-headline">
          <span class="auth-layout__art-eyebrow">
            <span class="dot" />
            校园电信诈骗上报与预警平台
          </span>
          <h2 class="auth-layout__art-title">
            反诈，<br>
            是我们一起做的事。
          </h2>
          <p class="auth-layout__art-lead">
            学生、辅导员、保卫处、系统管理员 ── 在同一个平台协作，
            <strong>事件报得快、流转得清、预警到得到。</strong>
          </p>
        </div>

        <ul class="auth-layout__features">
          <li
            v-for="(f, i) in features"
            :key="f.title"
            class="auth-layout__feature"
            :style="{ animationDelay: `${0.08 * i}s` }"
          >
            <span class="auth-layout__feature-icon">
              <AppIcon
                :name="(f.icon as never)"
                :size="20"
              />
            </span>
            <div>
              <strong>{{ f.title }}</strong>
              <p>{{ f.desc }}</p>
            </div>
            <span class="auth-layout__feature-no">0{{ i + 1 }}</span>
          </li>
        </ul>

        <HeroIllustration class="auth-layout__hero" />

        <div class="auth-layout__art-foot">
          <span><AppIcon
            name="shield-check"
            :size="12"
          />等保三级</span>
          <span class="dot" />
          <span>《反电信网络诈骗法》</span>
          <span class="dot" />
          <span>2026 软件工程课程项目</span>
        </div>
      </div>
    </section>

    <!-- 右侧表单面板 -->
    <section class="auth-layout__panel">
      <div class="auth-layout__panel-bg" />
      <header class="auth-layout__header">
        <BrandLogo
          :size="32"
          variant="color"
        />
        <span
          v-if="eyebrow"
          class="auth-layout__eyebrow"
        >
          {{ eyebrow }}
        </span>
      </header>
      <div class="auth-layout__card u-fade-up">
        <slot name="title">
          <h1 class="auth-layout__title">
            登录平台
          </h1>
        </slot>
        <p
          v-if="subtitle"
          class="auth-layout__subtitle"
        >
          {{ subtitle }}
        </p>
        <div class="auth-layout__body">
          <slot />
        </div>
      </div>
      <footer class="auth-layout__footer">
        <span>
          © {{ new Date().getFullYear() }} 南开大学 · 校园电信诈骗上报与预警平台
        </span>
        <span class="auth-layout__footer-links">
          <a href="#privacy">隐私声明</a>
          <span aria-hidden="true">·</span>
          <a href="#help">使用帮助</a>
          <span aria-hidden="true">·</span>
          <a href="https://www.nankai.edu.cn">南开主页 ↗</a>
        </span>
      </footer>
    </section>
  </main>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  background: var(--color-bg);
  position: relative;
}

@media (width <= 1024px) {
  .auth-layout {
    grid-template-columns: 1fr;
  }

  .auth-layout__art {
    display: none;
  }
}

/* ── 左侧叙事栏 ─────────────────────────────────────────────── */
.auth-layout__art {
  position: relative;
  overflow: hidden;
  background: var(--gradient-aurora);
  color: var(--color-neutral-0);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8) var(--space-7);
}

.auth-layout__art-grid {
  position: absolute;
  inset: 0;
  background-image: var(--pattern-grid);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse at 30% 30%, black 20%, transparent 75%);
  pointer-events: none;
  opacity: 0.85;
}

.auth-layout__art-noise {
  position: absolute;
  inset: 0;
  background-image:
    var(--pattern-lotus),
    var(--pattern-noise);
  background-size: 240px 240px, 160px 160px;
  background-position: 50% 60%, 0 0;
  background-repeat: repeat, repeat;
  opacity: 0.55;
  mix-blend-mode: overlay;
  pointer-events: none;
}

/* 八瓣莲花暗纹（南开校徽元素） */
.auth-layout__art::before {
  content: "";
  position: absolute;
  left: -120px;
  top: 30%;
  width: 480px;
  height: 480px;
  background-image: var(--pattern-lotus);
  background-size: 480px 480px;
  background-repeat: no-repeat;
  opacity: 0.62;
  pointer-events: none;
  mix-blend-mode: screen;
}

.auth-layout__art-motto {
  position: absolute;
  right: -2vw;
  bottom: 6vh;
  font-family: var(--font-family-serif);
  font-size: clamp(80px, 11vw, 160px);
  font-weight: 700;
  line-height: 0.95;
  letter-spacing: 0.08em;
  color: rgb(255 255 255 / 4%);
  white-space: nowrap;
  pointer-events: none;
  user-select: none;
  text-shadow: 0 1px 0 rgb(255 255 255 / 8%);
  writing-mode: vertical-rl;
  z-index: 0;
}

.auth-layout__art-seal {
  position: absolute;
  top: var(--space-7);
  right: var(--space-7);
  width: 72px;
  height: 72px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: var(--gradient-seal);
  border: 2px solid rgb(255 233 196 / 50%);
  border-radius: 4px;
  font-family: var(--font-family-serif);
  font-weight: 700;
  font-size: 28px;
  color: #ffe9c4;
  box-shadow:
    0 2px 0 rgb(31 8 11 / 60%),
    var(--shadow-glow-brand),
    inset 0 0 0 1px rgb(255 233 196 / 18%);
  transform: rotate(-6deg);
  user-select: none;
  pointer-events: none;
  z-index: 1;
}

.auth-layout__art-seal span {
  display: flex;
  align-items: center;
  justify-content: center;
  text-shadow: 0 1px 2px rgb(31 8 11 / 60%);
}

.auth-layout__art-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  max-width: 520px;
  width: 100%;
}

.auth-layout__art-headline {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.auth-layout__art-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  font-weight: var(--font-weight-medium);
  color: rgb(255 233 196 / 86%);
  width: fit-content;
}

.auth-layout__art-eyebrow .dot,
.auth-layout__art-foot .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-gold-300);
  box-shadow: 0 0 8px rgb(230 179 73 / 60%);
}

.auth-layout__art-title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: clamp(32px, 4vw, 52px);
  line-height: 1.12;
  letter-spacing: -0.02em;
  font-weight: 700;
  text-shadow: 0 2px 24px rgb(0 0 0 / 32%);
}

.auth-layout__art-lead {
  margin: 0;
  font-size: var(--font-size-md);
  line-height: 1.75;
  color: rgb(255 255 255 / 78%);
  max-width: 480px;
}

.auth-layout__art-lead strong {
  color: rgb(255 233 196 / 92%);
  font-weight: var(--font-weight-medium);
}

.auth-layout__features {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.auth-layout__feature {
  position: relative;
  display: grid;
  grid-template-columns: 40px 1fr auto;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background:
    linear-gradient(180deg, rgb(255 255 255 / 9%), rgb(255 255 255 / 4%));
  border: 1px solid rgb(255 255 255 / 14%);
  border-radius: var(--radius-md);
  backdrop-filter: blur(var(--glass-blur));
  animation: feature-in 600ms var(--easing-out) both;
  transition: border-color var(--duration-base) var(--easing-out);
}

.auth-layout__feature:hover {
  border-color: rgb(230 179 73 / 36%);
}

@keyframes feature-in {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.auth-layout__feature-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background:
    radial-gradient(circle at 30% 20%, rgb(255 233 196 / 28%), rgb(255 255 255 / 6%));
  border: 1px solid rgb(230 179 73 / 28%);
  color: var(--color-gold-200);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.auth-layout__feature strong {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: #fff;
  letter-spacing: 0.02em;
}

.auth-layout__feature p {
  margin: 2px 0 0;
  font-size: var(--font-size-xs);
  color: rgb(255 255 255 / 70%);
  line-height: 1.6;
}

.auth-layout__feature-no {
  font-family: var(--font-family-mono);
  font-size: 11px;
  color: rgb(230 179 73 / 64%);
  letter-spacing: 0.08em;
}

.auth-layout__hero {
  position: absolute;
  right: -60px;
  bottom: -80px;
  width: 380px;
  pointer-events: none;
  opacity: 0.5;
  z-index: 0;
}

.auth-layout__art-foot {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  font-size: 11px;
  color: rgb(255 255 255 / 56%);
  letter-spacing: 0.06em;
}

.auth-layout__art-foot span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* ── 右侧表单栏 ─────────────────────────────────────────────── */
.auth-layout__panel {
  display: flex;
  flex-direction: column;
  padding: var(--space-6) clamp(var(--space-5), 4vw, var(--space-8));
  background: var(--color-surface);
  position: relative;
  overflow: hidden;
}

.auth-layout__panel-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(at 100% 0%, rgb(134 38 51 / 5%), transparent 35%),
    radial-gradient(at 0% 100%, rgb(160 120 35 / 4%), transparent 40%);
  pointer-events: none;
}

.auth-layout__panel::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: var(--pattern-noise);
  background-size: 160px 160px;
  opacity: 0.08;
  mix-blend-mode: multiply;
  pointer-events: none;
}

.auth-layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.auth-layout__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-family-mono);
  font-size: 10.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: var(--font-weight-bold);
  padding: 5px 10px 5px 10px;
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, var(--color-gold-50) 0%, var(--color-gold-100) 100%);
  color: var(--color-gold-700);
  border: 1px solid rgb(230 179 73 / 56%);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    0 2px 6px -2px rgb(160 120 35 / 24%);
}

.auth-layout__eyebrow::before {
  content: "";
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-gold-500);
  box-shadow: 0 0 6px var(--color-gold-300);
}

.auth-layout__card {
  position: relative;
  z-index: 1;
  margin: auto 0;
  padding: var(--space-7) clamp(var(--space-5), 4vw, var(--space-7));
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    var(--shadow-mid);
  max-width: 480px;
  width: 100%;
}

.auth-layout__card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background: linear-gradient(
    180deg,
    rgb(134 38 51 / 4%) 0%,
    transparent 8%,
    transparent 92%,
    rgb(134 38 51 / 3%) 100%
  );
}

.auth-layout__title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.02em;
  color: var(--color-text-strong);
}

.auth-layout__subtitle {
  margin: var(--space-2) 0 var(--space-5);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}

.auth-layout__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.auth-layout__footer {
  position: relative;
  z-index: 1;
  margin-top: var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  flex-wrap: wrap;
  gap: var(--space-3);
}

.auth-layout__footer-links {
  display: inline-flex;
  gap: var(--space-2);
  align-items: center;
}

.auth-layout__footer-links a {
  color: var(--color-text-secondary);
  text-decoration: none;
}

.auth-layout__footer-links a:hover {
  color: var(--color-brand-700);
  text-decoration: underline;
}
</style>
