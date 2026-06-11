<!-- frontend/src/components/common/LoadingSpinner.vue — 加载动画组件（全屏/内联） -->
<template>
  <div
    v-if="visible"
    class="flex items-center justify-center"
    :class="fullscreen ? 'fixed inset-0 bg-white/80 dark:bg-gray-900/80 z-50' : 'py-8'"
  >
    <div class="flex flex-col items-center gap-3">
      <svg class="animate-spin h-8 w-8 text-[var(--color-primary-500)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      <span v-if="text" class="text-sm text-[var(--text-secondary)]">{{ text }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  visible?: boolean
  fullscreen?: boolean
  text?: string
}>()
</script>
