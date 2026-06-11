// frontend/src/composables/useCourse.ts — 课程上下文 Composable（当前课程信息缓存 + 角色判断）
import { computed } from 'vue'
import { useCourseStore } from '@/stores/course'

export function useCourse() {
  const store = useCourseStore()

  const courseId = computed(() => store.currentCourseId)
  const courseName = computed(() => store.currentCourseName)
  const myRole = computed(() => store.myRole)
  const isTeacher = computed(() => store.isTeacherOfCourse)
  const course = computed(() => store.currentCourse)

  function isActiveTab(tabName: string): boolean {
    // 由 Router 决定实际激活状态
    return true
  }

  return {
    courseId, courseName, myRole, isTeacher, course,
    isActiveTab,
  }
}
