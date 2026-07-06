<template>
  <!-- 图标通过name属性动态渲染 -->
  <svg v-if="name === 'chart'" :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="2" y="3" width="3" height="14" rx="1"/>
    <rect x="8" y="8" width="3" height="9" rx="1"/>
    <rect x="14" y="5" width="3" height="12" rx="1"/>
  </svg>

  <svg v-if="name === 'dashboard'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="1" y="1" width="6" height="6" rx="1"/>
    <rect x="9" y="1" width="6" height="6" rx="1"/>
    <rect x="1" y="9" width="6" height="6" rx="1"/>
    <rect x="9" y="9" width="6" height="6" rx="1"/>
  </svg>

  <svg v-if="name === 'holdings'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M2 4h12M2 8h12M2 12h12"/>
    <circle cx="4" cy="4" r="2" fill="currentColor"/>
    <circle cx="8" cy="8" r="2" fill="currentColor"/>
    <circle cx="12" cy="12" r="2" fill="currentColor"/>
  </svg>

  <svg v-if="name === 'kline'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <line x1="8" y1="1" x2="8" y2="4"/>
    <rect x="4" y="4" width="8" height="4" rx="1"/>
    <line x1="8" y1="8" x2="8" y2="12"/>
  </svg>

  <svg v-if="name === 'news'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="1" y="2" width="14" height="12" rx="2"/>
    <line x1="3" y1="5" x2="13" y2="5"/>
    <line x1="3" y1="8" x2="10" y2="8"/>
    <line x1="3" y1="11" x2="8" y2="11"/>
  </svg>

  <svg v-if="name === 'ai'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="8" cy="8" r="6"/>
    <circle cx="5" cy="6" r="1" fill="currentColor"/>
    <circle cx="11" cy="6" r="1" fill="currentColor"/>
    <path d="M5 10 Q8 12 11 10"/>
  </svg>

  <svg v-if="name === 'settings'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="8" cy="8" r="3"/>
    <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.5 3.5l1.4 1.4M11.1 11.1l1.4 1.4M3.5 12.5l1.4-1.4M11.1 4.9l1.4-1.4"/>
  </svg>

  <svg v-if="name === 'money'" :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="10" cy="10" r="8"/>
    <path d="M10 6v8M6 10h8"/>
  </svg>

  <svg v-if="name === 'down'" :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M3 8l5 5 4-4 5 5"/>
    <path d="M17 14v-4"/>
  </svg>

  <svg v-if="name === 'warning'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M8 1l7 14H1L8 1z"/>
    <line x1="8" y1="6" x2="8" y2="9"/>
    <circle cx="8" cy="12" r="1" fill="currentColor"/>
  </svg>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 }
});
</script>