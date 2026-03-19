import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'

interface Creator {
  id: string
  email: string
  youtube_channel_name?: string
  avatar_url?: string
  total_exams: number
  total_users: number
}

export const useCreatorStore = defineStore('creator', () => {
  const token = ref<string>(localStorage.getItem('creator_token') || '')
  const user = ref<Creator | null>(null)
  const isLoggedIn = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const res: any = await authAPI.login({ email, password })
    token.value = res.data?.token || res.token
    localStorage.setItem('creator_token', token.value)
    user.value = res.data?.creator || res.creator
    return user.value
  }

  async function fetchUser() {
    if (!token.value) return null
    try {
      const res: any = await authAPI.getCurrentUser()
      user.value = res.data || res
      return user.value
    } catch (error) {
      logout()
      return null
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('creator_token')
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    fetchUser,
    logout
  }
})
