<script setup lang="ts">
/**
 * 登录页装饰图：守护盾 + 雷达 + 数据脉络复合插画。
 * - 多层光环 + 八瓣莲花轮廓（南开符号）；
 * - 节点信号沿环形脉络流动，象征「上报 → 流转 → 闭环」；
 * - 盾牌中央嵌「✓」核验标识；
 * - 完全 SVG，受 prefers-reduced-motion 控制。
 */
</script>

<template>
  <div
    class="hero"
    aria-hidden="true"
  >
    <svg
      viewBox="0 0 520 520"
      class="hero__svg"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <radialGradient
          id="hero-bg"
          cx="50%"
          cy="50%"
          r="50%"
        >
          <stop
            offset="0%"
            stop-color="rgba(255,225,200,0.18)"
          />
          <stop
            offset="60%"
            stop-color="rgba(134,38,51,0.10)"
          />
          <stop
            offset="100%"
            stop-color="rgba(255,255,255,0)"
          />
        </radialGradient>
        <linearGradient
          id="hero-sweep"
          x1="0"
          y1="0"
          x2="1"
          y2="0"
        >
          <stop
            offset="0%"
            stop-color="rgba(230,179,73,0)"
          />
          <stop
            offset="65%"
            stop-color="rgba(230,179,73,0.55)"
          />
          <stop
            offset="100%"
            stop-color="rgba(255,255,255,0)"
          />
        </linearGradient>
        <linearGradient
          id="hero-shield"
          x1="0"
          y1="0"
          x2="0.6"
          y2="1"
        >
          <stop
            offset="0%"
            stop-color="#ffffff"
          />
          <stop
            offset="60%"
            stop-color="#f4d4dc"
          />
          <stop
            offset="100%"
            stop-color="#e69aa3"
          />
        </linearGradient>
        <filter
          id="hero-glow"
          x="-50%"
          y="-50%"
          width="200%"
          height="200%"
        >
          <feGaussianBlur stdDeviation="6" />
        </filter>
        <filter
          id="hero-soft"
          x="-50%"
          y="-50%"
          width="200%"
          height="200%"
        >
          <feGaussianBlur stdDeviation="2" />
        </filter>
      </defs>

      <!-- 背景圆光晕 -->
      <circle
        cx="260"
        cy="260"
        r="240"
        fill="url(#hero-bg)"
      />

      <!-- 同心环 + 金色虚线箍 -->
      <circle
        cx="260"
        cy="260"
        r="220"
        fill="none"
        stroke="rgba(255,255,255,0.10)"
        stroke-width="1"
      />
      <circle
        cx="260"
        cy="260"
        r="180"
        fill="none"
        stroke="rgba(230,179,73,0.22)"
        stroke-width="0.8"
        stroke-dasharray="2 4"
      />
      <circle
        cx="260"
        cy="260"
        r="140"
        fill="none"
        stroke="rgba(255,255,255,0.16)"
        stroke-width="1"
      />
      <circle
        cx="260"
        cy="260"
        r="100"
        fill="rgba(255,255,255,0.04)"
        stroke="rgba(230,179,73,0.32)"
        stroke-width="0.6"
        stroke-dasharray="0.8 2"
      />

      <!-- 横纵十字线 -->
      <line
        x1="40"
        y1="260"
        x2="480"
        y2="260"
        stroke="rgba(255,255,255,0.08)"
        stroke-dasharray="3 6"
      />
      <line
        x1="260"
        y1="40"
        x2="260"
        y2="480"
        stroke="rgba(255,255,255,0.08)"
        stroke-dasharray="3 6"
      />

      <!-- 数据节点连线（环上脉络） -->
      <g
        class="hero__pulse"
        stroke="rgba(230,179,73,0.4)"
        stroke-width="0.8"
        fill="none"
      >
        <path d="M260 80 Q360 120 420 220" />
        <path d="M420 220 Q450 320 380 420" />
        <path d="M380 420 Q260 470 140 420" />
        <path d="M140 420 Q70 320 100 220" />
        <path d="M100 220 Q160 120 260 80" />
      </g>

      <!-- 节点（呼吸闪烁） -->
      <g class="hero__nodes">
        <circle
          cx="260"
          cy="80"
          r="4"
          fill="#ffd166"
        />
        <circle
          cx="420"
          cy="220"
          r="4"
          fill="#ff8a8a"
        />
        <circle
          cx="380"
          cy="420"
          r="4"
          fill="#ffd166"
        />
        <circle
          cx="140"
          cy="420"
          r="4"
          fill="#ff8a8a"
        />
        <circle
          cx="100"
          cy="220"
          r="4"
          fill="#ffd166"
        />
      </g>

      <!-- 威胁告警散点 -->
      <g class="hero__threats">
        <circle
          cx="180"
          cy="170"
          r="3.4"
          fill="#ff8a8a"
        />
        <circle
          cx="340"
          cy="180"
          r="2.8"
          fill="#ffd166"
        />
        <circle
          cx="358"
          cy="320"
          r="3.4"
          fill="#ff8a8a"
        />
        <circle
          cx="200"
          cy="340"
          r="2.8"
          fill="#ffd166"
        />
        <circle
          cx="290"
          cy="350"
          r="2.4"
          fill="#ff8a8a"
        />
      </g>

      <!-- 雷达扫描扇形 -->
      <g class="hero__sweep">
        <path
          d="M260 260 L480 260 A220 220 0 0 0 410 110 Z"
          fill="url(#hero-sweep)"
          opacity="0.55"
        />
      </g>

      <!-- 八瓣莲花轮廓（极淡 · 文化暗纹） -->
      <g
        transform="translate(260 260)"
        opacity="0.35"
      >
        <g
          v-for="i in 8"
          :key="i"
          :transform="`rotate(${(i - 1) * 45})`"
        >
          <path
            d="M0 -78 C12 -60 12 -32 0 -16 C-12 -32 -12 -60 0 -78 Z"
            fill="none"
            stroke="rgba(230,179,73,0.5)"
            stroke-width="0.6"
          />
        </g>
      </g>

      <!-- 中央守护盾 -->
      <g transform="translate(260 260)">
        <circle
          r="58"
          fill="rgba(255,255,255,0.08)"
          filter="url(#hero-glow)"
        />
        <circle
          r="56"
          fill="none"
          stroke="rgba(230,179,73,0.4)"
          stroke-width="0.8"
        />
        <path
          d="M0 -44 L32 -32 V0 C32 20 18 36 0 46 C-18 36 -32 20 -32 0 V-32 Z"
          fill="url(#hero-shield)"
        />
        <path
          d="M0 -44 L32 -32 V0 C32 20 18 36 0 46 C-18 36 -32 20 -32 0 V-32 Z"
          fill="none"
          stroke="rgba(134,38,51,0.4)"
          stroke-width="0.6"
        />
        <path
          d="M-11 0 L-3 8 L13 -10"
          fill="none"
          stroke="#862633"
          stroke-width="4"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </g>
    </svg>
  </div>
</template>

<style scoped>
.hero {
  position: relative;
  width: 100%;
  max-width: 460px;
  aspect-ratio: 1;
}

.hero__svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 16px 48px rgb(0 0 0 / 32%));
}

.hero__sweep {
  transform-origin: 260px 260px;
  animation: sweep 5.5s linear infinite;
}

.hero__nodes circle {
  animation: pulse-node 2.6s ease-in-out infinite;
  transform-origin: center;
  transform-box: fill-box;
}

.hero__nodes circle:nth-child(2) { animation-delay: 0.4s; }
.hero__nodes circle:nth-child(3) { animation-delay: 0.8s; }
.hero__nodes circle:nth-child(4) { animation-delay: 1.2s; }
.hero__nodes circle:nth-child(5) { animation-delay: 1.6s; }

.hero__threats circle {
  animation: pulse-threat 2.4s ease-in-out infinite;
  transform-origin: center;
  transform-box: fill-box;
}

.hero__threats circle:nth-child(2) { animation-delay: 0.4s; }
.hero__threats circle:nth-child(3) { animation-delay: 0.9s; }
.hero__threats circle:nth-child(4) { animation-delay: 1.3s; }
.hero__threats circle:nth-child(5) { animation-delay: 1.8s; }

.hero__pulse path {
  stroke-dasharray: 6 8;
  animation: dash 7s linear infinite;
}

@keyframes sweep {
  from { transform: rotate(0); }
  to { transform: rotate(360deg); }
}

@keyframes pulse-node {
  0%, 100% { opacity: 0.6; transform: scale(0.85); }
  50% { opacity: 1; transform: scale(1.4); }
}

@keyframes pulse-threat {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.5); }
}

@keyframes dash {
  to { stroke-dashoffset: -140; }
}

@media (prefers-reduced-motion: reduce) {
  .hero__sweep,
  .hero__nodes circle,
  .hero__threats circle,
  .hero__pulse path {
    animation: none;
  }
}
</style>
