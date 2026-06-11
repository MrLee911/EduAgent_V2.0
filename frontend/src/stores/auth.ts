// frontend/src/stores/auth.ts — 认证状态管理（Pinia Setup Store）
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, RegisterRequest, TokenData } from '@/types'
import client from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const isLoading = ref(false)

  // ── Getters ──
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')
  const isAdmin = computed(() => user.value?.role === 'admin')

  // ── Actions ──
  function setTokens(access: string, refresh: string) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    token.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(data: LoginRequest): Promise<void> {
    isLoading.value = true
    try {
      const res = await client.post<null, { data: TokenData }>('/auth/login', data)
      setTokens(res.data.access_token, res.data.refresh_token)
      user.value = res.data.user
    } finally {
      isLoading.value = false
    }
  }

  async function register(data: RegisterRequest): Promise<void> {
    isLoading.value = true
    try {
      const res = await client.post<null, { data: User }>('/auth/register', data)
      user.value = res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchMe(): Promise<void> {
    try {
      const res = await client.get<null, { data: User }>('/auth/me')
      user.value = res.data
    } catch {
      clearTokens()
      user.value = null
    }
  }

  async function updateProfile(data: Record<string, any>): Promise<void> {
    const res = await client.patch<null, { data: User }>('/auth/me', data)
    user.value = res.data
  }

  async function logout(): Promise<void> {
    try {
      await client.post('/auth/logout')
    } finally {
      clearTokens()
      user.value = null
    }
  }

  return {
    user, token, refreshToken, isLoading,
    isLoggedIn, isTeacher, isStudent, isAdmin,
    login, register, fetchMe, updateProfile, logout, clearTokens,
  }
})
