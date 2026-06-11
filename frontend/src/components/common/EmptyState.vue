<!-- frontend/src/components/common/EmptyState.vue — 空数据占位组件 -->
<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <div v-if="icon" class="text-5xl mb-4">{{ icon }}</div>
    <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-2">{{ title }}</h3>
    <p v-if="description" class="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
      {{ description }}
    </p>
    <router-link
      v-if="actionRoute"
      :to="actionRoute"
      class="px-4 py-2 bg-[var(--color-primary-500)] text-white text-sm rounded-lg hover:bg-[var(--color-primary-600)] transition-colors"
    >
      {{ actionLabel || '开始使用' }}
    </router-link>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  description?: string
  actionLabel?: string
  actionRoute?: string
}>()
</script>
