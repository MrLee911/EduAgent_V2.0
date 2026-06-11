<!-- frontend/src/components/common/MarkdownRenderer.vue — Markdown 渲染组件 -->
<template>
  <div class="prose prose-sm max-w-none dark:prose-invert" v-html="sanitizedHtml" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{
  content: string
}>()

const sanitizedHtml = computed(() => {
  if (!props.content) return ''
  const raw = marked.parse(props.content) as string
  return DOMPurify.sanitize(raw)
})
</script>
