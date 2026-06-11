<!-- frontend/src/components/common/ToastNotification.vue — Toast 通知容器 -->
<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      <transition-group name="toast">
        <div
          v-for="toast in toastList"
          :key="toast.id"
          class="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg min-w-[300px] max-w-[420px] animate-slide-in-right"
          :class="bgClass(toast.type)"
        >
          <!-- 图标 -->
          <span class="text-lg mt-0.5">{{ iconMap[toast.type] }}</span>

          <!-- 内容 -->
          <div class="flex-1 min-w-0">
            <p v-if="toast.title" class="text-sm font-semibold">{{ toast.title }}</p>
            <p class="text-sm">{{ toast.message }}</p>
          </div>

          <!-- 关闭 -->
          <button @click="removeToast(toast.id)" class="text-current opacity-50 hover:opacity-100 transition-opacity ml-2">
            ✕
          </button>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useToast } from '@/composables/useToast'
import type { Toast } from '@/types'

const { toasts, removeToast } = useToast()
const toastList = computed(() => toasts.value)

const iconMap: Record<Toast['type'], string> = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
}

function bgClass(type: Toast['type']): string {
  switch (type) {
    case 'success': return 'bg-green-50 text-green-800 border border-green-200'
    case 'error': return 'bg-red-50 text-red-800 border border-red-200'
    case 'warning': return 'bg-yellow-50 text-yellow-800 border border-yellow-200'
    case 'info': return 'bg-blue-50 text-blue-800 border border-blue-200'
    default: return 'bg-gray-50 text-gray-800 border border-gray-200'
  }
}
</script>

<style scoped>
.toast-enter-active { transition: all 400ms ease-out; }
.toast-leave-active { transition: all 300ms ease-in; }
.toast-enter-from { opacity: 0; transform: translateX(100%); }
.toast-leave-to { opacity: 0; transform: translateX(100%); }
</style>
