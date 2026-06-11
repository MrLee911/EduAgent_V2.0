<script setup lang="ts">
/**
 * AdminUsersView.vue — 管理后台-用户管理 (T8.12)
 * 用户搜索 + 过滤 + 表格 + 启用/禁用
 */
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { User } from '@/types'

const toast = useToast()

// ── State ──
const users = ref<User[]>([])
const isLoading = ref(false)
const loadError = ref('')
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')

// ── Methods ──
async function fetchUsers() {
  isLoading.value = true
  loadError.value = ''
  try {
    const params: any = {}
    if (keyword.value) params.keyword = keyword.value
    if (roleFilter.value) params.role = roleFilter.value
    if (statusFilter.value !== '') params.is_active = statusFilter.value === 'active'
    const res = await adminApi.listUsers(params)
    users.value = res.data || []
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载用户列表失败'
  } finally {
    isLoading.value = false
  }
}

async function toggleUserStatus(user: User) {
  try {
    await adminApi.updateUser(user.id, { is_active: !user.is_active })
    toast.success(user.is_active ? '用户已禁用' : '用户已启用')
    await fetchUsers()
  } catch (e: any) {
    toast.error(`操作失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

function getRoleLabel(role: string) {
  const map: Record<string, string> = { teacher: '教师', student: '学生', admin: '管理员' }
  return map[role] || role
}

function getRoleBadgeClass(role: string) {
  const map: Record<string, string> = {
    admin: 'bg-purple-50 text-purple-700',
    teacher: 'bg-blue-50 text-blue-700',
    student: 'bg-green-50 text-green-700',
  }
  return map[role] || 'bg-gray-50 text-gray-600'
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(fetchUsers)
</script>

<template>
  <div class="p-4 space-y-4">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-semibold text-gray-800">👥 用户管理</h2>
      <p class="text-sm text-gray-500 mt-0.5">管理系统用户和权限</p>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2">
      <input
        v-model="keyword"
        @input="fetchUsers"
        placeholder="搜索用户名或邮箱..."
        class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40 w-56"
      />
      <select v-model="roleFilter" @change="fetchUsers" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white">
        <option value="">全部角色</option>
        <option value="admin">管理员</option>
        <option value="teacher">教师</option>
        <option value="student">学生</option>
      </select>
      <select v-model="statusFilter" @change="fetchUsers" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white">
        <option value="">全部状态</option>
        <option value="active">已启用</option>
        <option value="inactive">已禁用</option>
      </select>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" text="加载用户列表..." />

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <p class="text-red-500 text-sm mb-3">{{ loadError }}</p>
      <button @click="fetchUsers" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="users.length === 0"
      icon="👥"
      title="没有找到用户"
      description="暂无符合筛选条件的用户"
    />

    <!-- User Table -->
    <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-gray-600">用户名</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">显示名</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">邮箱</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">角色</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">状态</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">注册时间</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="u in users" :key="u.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3 font-medium text-gray-800">{{ u.username }}</td>
              <td class="px-4 py-3 text-gray-600">{{ u.display_name || '-' }}</td>
              <td class="px-4 py-3 text-gray-500 text-xs">{{ u.email }}</td>
              <td class="px-4 py-3">
                <span :class="['px-2 py-0.5 rounded text-xs', getRoleBadgeClass(u.role)]">
                  {{ getRoleLabel(u.role) }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span :class="[
                  'inline-block w-2 h-2 rounded-full mr-1.5',
                  u.is_active ? 'bg-green-500' : 'bg-gray-300'
                ]"></span>
                <span class="text-xs" :class="u.is_active ? 'text-green-600' : 'text-gray-400'">
                  {{ u.is_active ? '已启用' : '已禁用' }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-400 text-xs">{{ formatDate(u.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <button
                  @click="toggleUserStatus(u)"
                  :class="[
                    'text-xs font-medium transition-colors',
                    u.is_active
                      ? 'text-red-500 hover:text-red-700'
                      : 'text-green-600 hover:text-green-800'
                  ]"
                >
                  {{ u.is_active ? '禁用' : '启用' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
