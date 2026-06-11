<script setup lang="ts">
/**
 * ProfileView.vue — 个人中心页 (T8.14)
 * 个人信息 + 修改密码
 */
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import client from '@/api/client'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const authStore = useAuthStore()
const toast = useToast()

const user = computed(() => authStore.user)

// ── Profile Form ──
const displayName = ref('')
const email = ref('')
const isSavingProfile = ref(false)

// ── Password Form ──
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isChangingPassword = ref(false)

// ── State ──
const isLoading = ref(false)
const loadError = ref('')

function getRoleLabel(role: string) {
  const map: Record<string, string> = { teacher: '教师', student: '学生', admin: '管理员' }
  return map[role] || role
}

async function loadProfile() {
  isLoading.value = true
  loadError.value = ''
  try {
    await authStore.fetchMe()
    if (user.value) {
      displayName.value = user.value.display_name || ''
      email.value = user.value.email
    }
  } catch (e: any) {
    loadError.value = '加载个人信息失败'
  } finally {
    isLoading.value = false
  }
}

async function handleSaveProfile() {
  isSavingProfile.value = true
  try {
    await client.patch('/auth/me', {
      display_name: displayName.value,
      email: email.value,
    })
    await authStore.fetchMe()
    toast.success('个人信息已更新')
  } catch (e: any) {
    toast.error(`保存失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isSavingProfile.value = false
  }
}

async function handleChangePassword() {
  if (!currentPassword.value) {
    toast.warning('请输入当前密码')
    return
  }
  if (newPassword.value.length < 6) {
    toast.warning('新密码长度至少 6 位')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    toast.warning('两次输入的密码不一致')
    return
  }

  isChangingPassword.value = true
  try {
    await client.post('/auth/change-password', {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })
    toast.success('密码修改成功')
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e: any) {
    toast.error(`修改失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isChangingPassword.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <div class="max-w-2xl mx-auto p-4 space-y-6">
    <h2 class="text-lg font-semibold text-gray-800">👤 个人中心</h2>

    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" text="加载个人信息..." />

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <p class="text-red-500 text-sm mb-3">{{ loadError }}</p>
      <button @click="loadProfile" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
    </div>

    <template v-else-if="user">
      <!-- Avatar & Basic Info -->
      <div class="bg-white rounded-lg border border-gray-200 p-4">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center text-2xl">
            {{ (user.display_name || user.username).charAt(0).toUpperCase() }}
          </div>
          <div>
            <h3 class="font-semibold text-gray-800">{{ user.display_name || user.username }}</h3>
            <p class="text-sm text-gray-500">@{{ user.username }}</p>
            <span class="inline-block mt-1 px-2 py-0.5 text-xs rounded"
              :class="user.role === 'admin' ? 'bg-purple-50 text-purple-700' : user.role === 'teacher' ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'">
              {{ getRoleLabel(user.role) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Profile Form -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h3 class="font-semibold text-gray-800 text-sm">基本信息</h3>
        <div>
          <label class="block text-sm text-gray-600 mb-1">用户名</label>
          <input :value="user.username" disabled class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-gray-50 text-gray-500" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">显示名称</label>
          <input v-model="displayName" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">邮箱</label>
          <input v-model="email" type="email" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">角色</label>
          <input :value="getRoleLabel(user.role)" disabled class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-gray-50 text-gray-500" />
        </div>
        <div class="flex justify-end">
          <button
            @click="handleSaveProfile"
            :disabled="isSavingProfile"
            class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 transition-colors"
          >
            {{ isSavingProfile ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>

      <!-- Change Password -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h3 class="font-semibold text-gray-800 text-sm">🔒 修改密码</h3>
        <div>
          <label class="block text-sm text-gray-600 mb-1">当前密码</label>
          <input v-model="currentPassword" type="password" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">新密码</label>
          <input v-model="newPassword" type="password" placeholder="至少 6 位" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">确认新密码</label>
          <input v-model="confirmPassword" type="password" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
        </div>
        <div class="flex justify-end">
          <button
            @click="handleChangePassword"
            :disabled="isChangingPassword"
            class="px-4 py-2 bg-gray-800 text-white rounded-lg text-sm font-medium hover:bg-gray-900 disabled:opacity-50 transition-colors"
          >
            {{ isChangingPassword ? '修改中...' : '修改密码' }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
