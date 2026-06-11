<!-- frontend/src/components/common/ConfirmDialog.vue — 确认对话框组件 -->
<template>
  <Teleport to="body">
    <transition name="modal">
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="handleCancel"
      >
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6 animate-modal-enter">
          <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ title }}</h3>
          <p v-if="message" class="text-sm text-gray-500 mb-6">{{ message }}</p>
          <div v-if="$slots.default" class="mb-4">
            <slot></slot>
          </div>

          <div class="flex justify-end gap-3">
            <button
              @click="handleCancel"
              class="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              取消
            </button>
            <button
              @click="handleConfirm"
              class="px-4 py-2 text-sm text-white rounded-lg transition-colors"
              :class="danger ? 'bg-red-500 hover:bg-red-600' : 'bg-primary-500 hover:bg-primary-600'"
            >
              {{ confirmText || '确认' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  message?: string
  confirmText?: string
  danger?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function handleConfirm() { emit('confirm') }
function handleCancel() { emit('cancel') }
</script>

<style scoped>
.modal-enter-active { transition: opacity 300ms cubic-bezier(0.16,1,0.3,1); }
.modal-leave-active { transition: opacity 200ms ease-in; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
