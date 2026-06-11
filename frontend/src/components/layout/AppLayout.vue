<!-- frontend/src/components/layout/AppLayout.vue — 全局布局壳（Header + Sidebar + Content + Toast） -->
<template>
  <div class="flex flex-col h-screen">
    <!-- Header -->
    <AppHeader />

    <!-- Body -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar（仅课程子页面显示） -->
      <AppSidebar v-if="showSidebar" />

      <!-- 主内容区 -->
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>

    <!-- Toast 容器 -->
    <ToastNotification />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import ToastNotification from '@/components/common/ToastNotification.vue'

const route = useRoute()
const showSidebar = computed(() => {
  return route.params.courseId && !route.path.includes('/login') && !route.path.includes('/register')
})
</script>
