<script setup lang="ts">
/**
 * 品牌徽标 · Anti-Fraud Platform · 南开大学校园电信诈骗上报与预警平台
 *
 * 视觉构造：
 *   · 主体「盾」取自校徽轮廓化简，左肩抹「青莲紫」、右下沉「玄黑」；
 *   · 盾内「八瓣莲花」呼应南开「以莲为徽」的传统，花蕊嵌「✓」象征核验通过；
 *   · 外环极细金箍线表「等保三级」「合规闭环」；
 *   · 题字采用衬线 + 雅黑分层（避免 AI 通病的「单一无衬线」）。
 */
interface Props {
  size?: number;
  variant?: "color" | "mono" | "white";
  withText?: boolean;
  textVariant?: "stack" | "inline";
}

withDefaults(defineProps<Props>(), {
  size: 28,
  variant: "color",
  withText: true,
  textVariant: "stack",
});
</script>

<template>
  <span
    class="brand-logo"
    :class="[`brand-logo--${variant}`, `brand-logo--text-${textVariant}`]"
  >
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 64 64"
      role="img"
      aria-label="校园电信诈骗上报与预警平台 · 南开大学"
      class="brand-logo__mark"
    >
      <defs>
        <linearGradient
          id="brand-shield-fill"
          x1="0"
          y1="0"
          x2="1"
          y2="1"
        >
          <stop
            offset="0%"
            stop-color="#b03145"
          />
          <stop
            offset="55%"
            stop-color="#862633"
          />
          <stop
            offset="100%"
            stop-color="#3a1015"
          />
        </linearGradient>
        <linearGradient
          id="brand-shield-sheen"
          x1="0"
          y1="0"
          x2="0.6"
          y2="1"
        >
          <stop
            offset="0%"
            stop-color="rgba(255,255,255,0.32)"
          />
          <stop
            offset="55%"
            stop-color="rgba(255,255,255,0)"
          />
        </linearGradient>
        <linearGradient
          id="brand-lotus"
          x1="0"
          y1="0"
          x2="0"
          y2="1"
        >
          <stop
            offset="0%"
            stop-color="#fde7c4"
          />
          <stop
            offset="60%"
            stop-color="#e6b349"
          />
          <stop
            offset="100%"
            stop-color="#a07823"
          />
        </linearGradient>
        <filter
          id="brand-soft"
          x="-30%"
          y="-30%"
          width="160%"
          height="160%"
        >
          <feGaussianBlur stdDeviation="0.6" />
        </filter>
      </defs>

      <path
        d="M32 4 L54 11 V26.5 C54 41.6 45.2 53.4 32 60 C18.8 53.4 10 41.6 10 26.5 V11 Z"
        fill="url(#brand-shield-fill)"
      />
      <path
        d="M32 4 L54 11 V26.5 C54 41.6 45.2 53.4 32 60 C18.8 53.4 10 41.6 10 26.5 V11 Z"
        fill="url(#brand-shield-sheen)"
        opacity="0.85"
      />
      <path
        d="M32 4 L54 11 V26.5 C54 41.6 45.2 53.4 32 60 C18.8 53.4 10 41.6 10 26.5 V11 Z"
        fill="none"
        stroke="rgba(255,255,255,0.22)"
        stroke-width="0.6"
      />
      <path
        d="M32 8.6 L50 14.7 V26 C50 39 42.4 49.5 32 55.5 C21.6 49.5 14 39 14 26 V14.7 Z"
        fill="none"
        stroke="rgba(230,179,73,0.42)"
        stroke-width="0.5"
        stroke-dasharray="0.8 1.4"
      />

      <g
        transform="translate(32 30)"
        filter="url(#brand-soft)"
      >
        <g
          v-for="i in 8"
          :key="i"
          :transform="`rotate(${(i - 1) * 45})`"
        >
          <path
            d="M0 -14 C2.4 -10.6 2.4 -5 0 -1 C-2.4 -5 -2.4 -10.6 0 -14 Z"
            fill="url(#brand-lotus)"
            opacity="0.92"
          />
        </g>
        <circle
          r="3.8"
          fill="#fff8e7"
        />
        <circle
          r="3.8"
          fill="none"
          stroke="rgba(160,120,35,0.55)"
          stroke-width="0.4"
        />
        <path
          d="M-1.8 0 L-0.4 1.4 L2.2 -1.6"
          fill="none"
          stroke="#862633"
          stroke-width="1.2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </g>
    </svg>

    <span
      v-if="withText"
      class="brand-logo__text"
    >
      <strong>反诈守护</strong>
      <small>NANKAI · 校园反诈平台</small>
    </span>
  </span>
</template>

<style scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  font-family: var(--font-family-sans);
}

.brand-logo--text-inline {
  align-items: center;
}

.brand-logo__mark {
  filter:
    drop-shadow(0 4px 8px rgb(134 38 51 / 22%))
    drop-shadow(0 1px 0 rgb(255 255 255 / 25%));
}

.brand-logo__text {
  display: inline-flex;
  flex-direction: column;
  line-height: 1.1;
}

.brand-logo--text-inline .brand-logo__text {
  flex-direction: row;
  align-items: baseline;
  gap: var(--space-2);
}

.brand-logo__text strong {
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.06em;
  color: var(--color-text-strong);
}

.brand-logo__text small {
  font-size: 10.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.brand-logo--white .brand-logo__text strong {
  color: #fff;
  text-shadow: 0 1px 2px rgb(0 0 0 / 24%);
}

.brand-logo--white .brand-logo__text small {
  color: rgb(255 233 196 / 78%);
}

.brand-logo--mono .brand-logo__mark {
  filter: grayscale(1) brightness(0.9);
}

.brand-logo--mono .brand-logo__text strong {
  color: var(--color-text-strong);
}
</style>
