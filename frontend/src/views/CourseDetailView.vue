<!-- frontend/src/views/CourseDetailView.vue — 课程详情容器页（阶段八完善） -->
<template>
  <div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const courseStore = useCourseStore()
const authStore = useAuthStore()

watch(
  () => [route.params.courseId, authStore.user?.id],
  async ([courseId]) => {
    const id = String(courseId || '')
    if (!id) {
      courseStore.setCurrentCourse(null)
      return
    }

    courseStore.setCurrentCourse(null)
    await courseStore.fetchCourseDetail(id)
  },
  { immediate: true },
)
</script>
