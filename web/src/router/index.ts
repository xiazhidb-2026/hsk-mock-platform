import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '数据看板' }
      },
      {
        path: 'questions',
        name: 'Questions',
        component: () => import('@/views/questions/QuestionList.vue'),
        meta: { title: '题目管理' }
      },
      {
        path: 'questions/create',
        name: 'QuestionCreate',
        component: () => import('@/views/questions/QuestionCreate.vue'),
        meta: { title: '创建题目' }
      },
      {
        path: 'templates',
        name: 'Templates',
        component: () => import('@/views/templates/TemplateList.vue'),
        meta: { title: '试卷管理' }
      },
      {
        path: 'templates/create',
        name: 'TemplateCreate',
        component: () => import('@/views/templates/TemplateCreate.vue'),
        meta: { title: '创建试卷' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/analytics/Analytics.vue'),
        meta: { title: '数据分析' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: { title: '个人设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('creator_token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
