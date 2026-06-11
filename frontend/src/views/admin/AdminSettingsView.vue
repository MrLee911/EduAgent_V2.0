<script setup lang="ts">
/**
 * AdminSettingsView.vue — 管理后台-系统设置 (T8.13)
 * AI模型配置 + RAG配置 + 系统配置
 */
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import type { AdminSettings } from '@/api/admin'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const toast = useToast()

// ── State ──
const isLoading = ref(false)
const loadError = ref('')
const isSaving = ref(false)

// AI Model Settings
const llmModel = ref('')
const llmBaseUrl = ref('')
const llmApiKeyMasked = ref('')
const llmMaxTokens = ref(4096)
const llmTemperature = ref(0.7)

// RAG Settings
const embeddingModel = ref('')
const chunkSize = ref(500)
const chunkOverlap = ref(50)
const topK = ref(5)
const similarityThreshold = ref(0.7)

// System Settings
const maxUploadSizeMb = ref(50)
const conversationRetentionDays = ref(30)
const defaultLanguage = ref('zh')

// ── Methods ──
async function loadSettings() {
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await adminApi.getSettings()
    if (res.data) {
      const s = res.data
      llmModel.value = s.llm_model
      llmBaseUrl.value = s.llm_base_url
      llmApiKeyMasked.value = s.llm_api_key_masked
      llmMaxTokens.value = s.llm_max_tokens
      llmTemperature.value = s.llm_temperature
      embeddingModel.value = s.embedding_model
      chunkSize.value = s.chunk_size
      chunkOverlap.value = s.chunk_overlap
      topK.value = s.top_k
      similarityThreshold.value = s.similarity_threshold
      maxUploadSizeMb.value = s.max_upload_size_mb
      conversationRetentionDays.value = s.conversation_retention_days
      defaultLanguage.value = s.default_language
    }
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载系统设置失败'
  } finally {
    isLoading.value = false
  }
}

async function handleSave() {
  isSaving.value = true
  try {
    await adminApi.updateSettings({
      llm_model: llmModel.value,
      llm_base_url: llmBaseUrl.value,
      llm_max_tokens: llmMaxTokens.value,
      llm_temperature: llmTemperature.value,
      embedding_model: embeddingModel.value,
      chunk_size: chunkSize.value,
      chunk_overlap: chunkOverlap.value,
      top_k: topK.value,
      similarity_threshold: similarityThreshold.value,
      max_upload_size_mb: maxUploadSizeMb.value,
      conversation_retention_days: conversationRetentionDays.value,
      default_language: defaultLanguage.value,
    })
    toast.success('系统设置已更新')
  } catch (e: any) {
    toast.error(`保存失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isSaving.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <div class="p-4 space-y-6">
    <div>
      <h2 class="text-lg font-semibold text-gray-800">⚙️ 系统设置</h2>
      <p class="text-sm text-gray-500 mt-0.5">管理 AI 模型、RAG 和系统参数</p>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" text="加载系统设置..." />

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <p class="text-red-500 text-sm mb-3">{{ loadError }}</p>
      <button @click="loadSettings" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
    </div>

    <template v-else>
      <!-- AI Model Settings -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h3 class="font-semibold text-gray-800">🤖 AI 模型配置</h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-gray-600 mb-1">模型名称</label>
            <input v-model="llmModel" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Base URL</label>
            <input v-model="llmBaseUrl" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">API Key</label>
            <input :value="llmApiKeyMasked" disabled class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-gray-50 text-gray-500" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Max Tokens</label>
            <input v-model.number="llmMaxTokens" type="number" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">Temperature: {{ llmTemperature }}</label>
          <input v-model.number="llmTemperature" type="range" min="0" max="2" step="0.1" class="w-full accent-primary-500" />
        </div>
      </div>

      <!-- RAG Settings -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h3 class="font-semibold text-gray-800">🔍 RAG 检索配置</h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-gray-600 mb-1">Embedding 模型</label>
            <input v-model="embeddingModel" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Top K</label>
            <input v-model.number="topK" type="number" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Chunk Size</label>
            <input v-model.number="chunkSize" type="number" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Chunk Overlap</label>
            <input v-model.number="chunkOverlap" type="number" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">相似度阈值: {{ similarityThreshold }}</label>
          <input v-model.number="similarityThreshold" type="range" min="0" max="1" step="0.05" class="w-full accent-primary-500" />
        </div>
      </div>

      <!-- System Settings -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h3 class="font-semibold text-gray-800">🖥️ 系统配置</h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-gray-600 mb-1">最大上传文件 (MB)</label>
            <input v-model.number="maxUploadSizeMb" type="number" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">对话保留天数</label>
            <input v-model.number="conversationRetentionDays" type="number" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">默认语言</label>
            <select v-model="defaultLanguage" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white">
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Save -->
      <div class="flex justify-end">
        <button
          @click="handleSave"
          :disabled="isSaving"
          class="px-6 py-2.5 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 transition-colors"
        >
          {{ isSaving ? '保存中...' : '保存全部设置' }}
        </button>
      </div>
    </template>
  </div>
</template>
