// frontend/src/stores/course.ts — 课程上下文状态管理（Pinia Setup Store）
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Course, CourseMember } from '@/types'
import client from '@/api/client'

export const useCourseStore = defineStore('course', () => {
  // ── State ──
  const currentCourse = ref<Course | null>(null)
  const courses = ref<Course[]>([])
  const members = ref<CourseMember[]>([])
  const isLoading = ref(false)

  // ── Getters ──
  const currentCourseId = computed(() => currentCourse.value?.id ?? '')
  const currentCourseName = computed(() => currentCourse.value?.name ?? '')
  const myRole = computed(() => currentCourse.value?.my_role ?? null)
  const isTeacherOfCourse = computed(() => myRole.value === 'teacher')

  // ── Actions ──
  async function fetchCourses(params?: Record<string, any>): Promise<void> {
    isLoading.value = true
    try {
      const res = await client.get<null, { data: Course[] }>('/courses', { params })
      courses.value = res.data ?? []
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCourseDetail(courseId: string): Promise<void> {
    isLoading.value = true
    try {
      const res = await client.get<null, { data: Course }>(`/courses/${courseId}`)
      currentCourse.value = res.data
    } finally {
      isLoading.value = false
    }
  }

  async function createCourse(data: { name: string; description?: string; semester?: string }): Promise<Course> {
    const res = await client.post<null, { data: Course }>('/courses', data)
    return res.data
  }

  async function joinCourse(courseCode: string): Promise<void> {
    await client.post('/courses/join', { course_code: courseCode })
  }

  async function fetchMembers(courseId: string): Promise<void> {
    const res = await client.get<null, { data: CourseMember[] }>(`/courses/${courseId}/members`)
    members.value = res.data ?? []
  }

  async function addStudent(courseId: string, identifier: string): Promise<CourseMember> {
    const res = await client.post<null, { data: CourseMember }>(`/courses/${courseId}/members`, { identifier })
    return res.data
  }

  async function removeMember(courseId: string, memberId: string): Promise<void> {
    await client.delete(`/courses/${courseId}/members/${memberId}`)
  }

  async function updateCourse(courseId: string, data: Record<string, any>): Promise<void> {
    await client.patch(`/courses/${courseId}`, data)
  }

  async function leaveCourse(courseId: string): Promise<void> {
    await client.delete(`/courses/${courseId}/members/me`)
  }

  async function deleteCourse(courseId: string, confirmText: string): Promise<void> {
    await client.delete(`/courses/${courseId}`, {
      data: { confirm: true, confirm_text: confirmText },
    })
  }

  function setCurrentCourse(course: Course | null) {
    currentCourse.value = course
  }

  return {
    currentCourse, courses, members, isLoading,
    currentCourseId, currentCourseName, myRole, isTeacherOfCourse,
    fetchCourses, fetchCourseDetail, createCourse, joinCourse,
    fetchMembers, addStudent, removeMember, updateCourse, leaveCourse, deleteCourse,
    setCurrentCourse,
  }
})
