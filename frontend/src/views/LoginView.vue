<!-- frontend/src/views/LoginView.vue — 登录页 -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-[var(--bg-page)] p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <span class="text-5xl">📚</span>
        <h1 class="text-3xl font-bold text-[var(--text-primary)] mt-3">EduAgent</h1>
        <p class="text-sm text-[var(--text-secondary)] mt-1">课程资源与教学任务智能体</p>
      </div>
      <div class="bg-[var(--bg-surface)] rounded-xl shadow-sm border border-[var(--border-light)] p-6">
        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--text-secondary)] mb-1">用户名 / 邮箱</label>
            <input
              v-model="form.username"
              type="text"
              placeholder="输入用户名"
              class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent"
              :disabled="loading"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text-secondary)] mb-1">密码</label>
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="输入密码"
              class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent"
              :disabled="loading"
            />
          </div>
          <button
            type="submit"
            class="w-full py-2.5 bg-[var(--color-primary-500)] text-white text-sm font-medium rounded-lg hover:bg-[var(--color-primary-600)] disabled:opacity-50 transition-colors btn-hover"
            :disabled="loading || !form.username || !form.password"
          >
            <span v-if="loading">登录中...</span>
            <span v-else>登 录</span>
          </button>
        </form>
        <p class="text-center text-sm text-[var(--text-secondary)] mt-4">
          没有账号？
          <router-link to="/register" class="text-[var(--color-primary-500)] hover:underline">立即注册</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ username: '', password: '' })
const showPassword = ref(false)
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await authStore.login(form)
    router.push('/home')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>
