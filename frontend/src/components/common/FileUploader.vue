<!-- frontend/src/components/common/FileUploader.vue — 文件拖拽上传组件 -->
<template>
  <div
    class="border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer"
    :class="isDragging ? 'border-[var(--color-primary-400)] bg-[var(--color-primary-50)]' : 'border-[var(--border-default)] hover:border-[var(--color-primary-300)]'"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
    @click="triggerFileInput"
  >
    <input
      ref="fileInputRef"
      type="file"
      class="hidden"
      :accept="acceptTypes"
      :multiple="multiple"
      @change="handleFileChange"
    />

    <div v-if="!isUploading" class="space-y-2">
      <div class="text-4xl">📁</div>
      <p class="text-sm text-[var(--text-secondary)]">
        {{ placeholder }}
      </p>
      <p class="text-xs text-[var(--text-muted)]">
        支持 {{ supportedTypes }}（单文件最大 {{ maxSizeMB }}MB）
      </p>
    </div>

    <div v-else class="space-y-3">
      <svg class="animate-spin h-8 w-8 text-[var(--color-primary-500)] mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      <p class="text-sm text-[var(--text-secondary)]">正在上传...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = withDefaults(defineProps<{
  placeholder?: string
  acceptTypes?: string
  supportedTypes?: string
  maxSizeMB?: number
  multiple?: boolean
}>(), {
  placeholder: '拖拽文件到此处或点击上传',
  acceptTypes: '.pdf,.docx,.pptx,.md,.txt,.xlsx',
  supportedTypes: 'PDF, DOCX, PPTX, MD, TXT, XLSX',
  maxSizeMB: 50,
  multiple: false,
})

const emit = defineEmits<{
  (e: 'files-selected', files: File[]): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    handleFiles(Array.from(input.files))
    input.value = ''
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files) {
    handleFiles(Array.from(e.dataTransfer.files))
  }
}

function handleFiles(files: File[]) {
  const validFiles = files.filter((f) => {
    const ext = f.name.split('.').pop()?.toLowerCase()
    if (!ext) return false
    if (f.size > props.maxSizeMB! * 1024 * 1024) return false
    return props.acceptTypes!.includes(ext)
  })

  if (validFiles.length > 0) {
    isUploading.value = true
    emit('files-selected', validFiles)
    setTimeout(() => { isUploading.value = false }, 2000)
  }
}
</script>
