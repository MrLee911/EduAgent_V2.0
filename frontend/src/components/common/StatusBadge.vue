<!-- frontend/src/components/common/StatusBadge.vue — 状态标签组件 -->
<template>
  <span
    class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full"
    :class="badgeClass"
  >
    <span v-if="showDot" class="w-1.5 h-1.5 rounded-full mr-1.5" :class="dotClass"></span>
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  status: string
  type?: 'resource' | 'task' | 'course' | 'generic'
  showDot?: boolean
}>(), {
  type: 'generic',
  showDot: true,
})

const statusMap: Record<string, { label: string; color: string; dot: string }> = {
  // 资源状态
  uploading: { label: '上传中', color: 'bg-blue-50 text-blue-700', dot: 'bg-blue-500' },
  parsing: { label: '解析中', color: 'bg-purple-50 text-purple-700', dot: 'bg-purple-500' },
  chunking: { label: '切片中', color: 'bg-indigo-50 text-indigo-700', dot: 'bg-indigo-500' },
  embedding: { label: '向量化', color: 'bg-pink-50 text-pink-700', dot: 'bg-pink-500' },
  ready: { label: '就绪', color: 'bg-green-50 text-green-700', dot: 'bg-green-500' },
  failed: { label: '失败', color: 'bg-red-50 text-red-700', dot: 'bg-red-500' },
  // 任务状态
  draft: { label: '草稿', color: 'bg-gray-50 text-gray-700', dot: 'bg-gray-400' },
  published: { label: '已发布', color: 'bg-green-50 text-green-700', dot: 'bg-green-500' },
  archived: { label: '已归档', color: 'bg-yellow-50 text-yellow-700', dot: 'bg-yellow-500' },
  // 课程状态
  active: { label: '进行中', color: 'bg-green-50 text-green-700', dot: 'bg-green-500' },
}

const badgeInfo = computed(() => {
  return statusMap[props.status] || { label: props.status, color: 'bg-gray-50 text-gray-700', dot: 'bg-gray-400' }
})

const label = computed(() => badgeInfo.value.label)
const badgeClass = computed(() => badgeInfo.value.color)
const dotClass = computed(() => badgeInfo.value.dot)
</script>
