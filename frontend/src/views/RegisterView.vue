<!-- frontend/src/views/RegisterView.vue — 注册页 -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-[var(--bg-page)] p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-[var(--text-primary)]">创建新账号</h1>
      </div>
      <div class="bg-[var(--bg-surface)] rounded-xl shadow-sm border border-[var(--border-light)] p-6">
        <form @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--text-secondary)] mb-1">用户名 *</label>
            <input v-model="form.username" type="text" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]" :disabled="loading" />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text-secondary)] mb-1">邮箱 *</label>
            <input v-model="form.email" type="email" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]" :disabled="loading" />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text-secondary)] mb-1">密码 *</label>
            <input v-model="form.password" type="password" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]" :disabled="loading" />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text-secondary)] mb-1">角色</label>
            <select v-model="form.role" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]">
              <option value="teacher">教师</option>
              <option value="student">学生</option>
            </select>
          </div>
          <button
            type="submit"
            class="w-full py-2.5 bg-[var(--color-primary-500)] text-white text-sm font-medium rounded-lg hover:bg-[var(--color-primary-600)] disabled:opacity-50 transition-colors btn-hover"
            :disabled="loading || !form.username || !form.email || !form.password"
          >
            <span v-if="loading">注册中...</span>
            <span v-else>注 册</span>
          </button>
        </form>
        <p class="text-center text-sm text-[var(--text-secondary)] mt-4">
          已有账号？
          <router-link to="/login" class="text-[var(--color-primary-500)] hover:underline">返回登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ username: '', email: '', password: '', role: 'teacher' as 'teacher' | 'student' })
const loading = ref(false)

async function handleRegister() {
  loading.value = true
  try {
    await authStore.register(form)
    router.push('/home')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>
