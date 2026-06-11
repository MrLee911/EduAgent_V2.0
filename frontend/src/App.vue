<!-- frontend/src/App.vue — 根组件 -->
<template>
  <router-view v-slot="{ Component, route }">
    <component :is="getLayout(route)">
      <component :is="Component" />
    </component>
  </router-view>
</template>

<script setup lang="ts">
import type { RouteLocationNormalized } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

function getLayout(route: RouteLocationNormalized) {
  // 登录/注册页面不使用布局壳
  if (route.path === '/login' || route.path === '/register') {
    return 'div'
  }
  return AppLayout
}
</script>
