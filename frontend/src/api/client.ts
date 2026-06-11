// frontend/src/api/client.ts — Axios 客户端（JWT 自动注入、统一解包、Token 刷新）
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse, TokenData } from '@/types'
import { useAuthStore } from '@/stores/auth'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── 请求拦截器：JWT 自动注入 ──
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── 响应拦截器：统一解包 + Token 过期自动刷新 ──
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(newToken: string) {
  refreshSubscribers.forEach((cb) => cb(newToken))
  refreshSubscribers = []
}

client.interceptors.response.use(
  (response): any => {
    return response.data as ApiResponse
  },
  async (error: AxiosError<ApiResponse>) => {
    const config = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Token 过期自动刷新
    if (error.response?.status === 401 && !config?._retry) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        useAuthStore().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            config.headers.Authorization = `Bearer ${newToken}`
            resolve(client.request(config) as any)
          })
        })
      }

      config._retry = true
      isRefreshing = true

      try {
        const res = await axios.post<ApiResponse>('/api/v1/auth/refresh', { refresh_token: refreshToken })
        const data = (res.data as any).data as { access_token: string; refresh_token: string }
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)

        onTokenRefreshed(data.access_token)
        isRefreshing = false

        config.headers.Authorization = `Bearer ${data.access_token}`
        return client.request(config) as any
      } catch {
        isRefreshing = false
        refreshSubscribers = []
        useAuthStore().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  },
)

export default client
