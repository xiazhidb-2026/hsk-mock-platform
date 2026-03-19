import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('creator_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.message || '请求失败'
    ElMessage.error(message)
    
    if (error.response?.status === 401) {
      localStorage.removeItem('creator_token')
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

export default api

// ============== 认证API ==============
export const authAPI = {
  login: (data: { email: string; password: string }) => 
    api.post('/creator/login', data),
  register: (data: any) => 
    api.post('/creator/register', data),
  getCurrentUser: () => 
    api.get('/creator/me')
}

// ============== 题目API ==============
export const questionAPI = {
  list: (params: any) => 
    api.get('/questions', { params }),
  get: (id: string) => 
    api.get(`/questions/${id}`),
  create: (data: any) => 
    api.post('/questions', data),
  update: (id: string, data: any) => 
    api.put(`/questions/${id}`, data),
  delete: (id: string) => 
    api.delete(`/questions/${id}`),
  import: (data: FormData) => 
    api.post('/questions/import', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
}

// ============== 试卷模板API ==============
export const templateAPI = {
  list: (params: any) => 
    api.get('/templates', { params }),
  get: (id: string) => 
    api.get(`/templates/${id}`),
  create: (data: any) => 
    api.post('/templates', data),
  update: (id: string, data: any) => 
    api.put(`/templates/${id}`, data),
  delete: (id: string) => 
    api.delete(`/templates/${id}`),
  publish: (id: string) => 
    api.post(`/templates/${id}/publish`)
}

// ============== 统计API ==============
export const statsAPI = {
  getDashboard: () => 
    api.get('/creator/stats'),
  getQuestionTypes: () => 
    api.get('/statistics/question-types')
}
