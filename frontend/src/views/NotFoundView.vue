<script setup lang="ts">
/**
 * NotFoundView.vue — 404 页面 (T8.15)
 */
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/home')
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
    <div class="text-center">
      <div class="text-8xl font-bold text-gray-200 mb-4">404</div>
      <h1 class="text-2xl font-bold text-gray-800 mb-2">页面未找到</h1>
      <p class="text-gray-500 mb-8">抱歉，您访问的页面不存在或已被移除</p>
      <div class="flex items-center justify-center gap-3">
        <button
          @click="goBack"
          class="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
        >
          ← 返回上页
        </button>
        <button
          @click="goHome"
          class="px-5 py-2.5 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
        >
          回到首页
        </button>
      </div>
    </div>
  </div>
</template>
