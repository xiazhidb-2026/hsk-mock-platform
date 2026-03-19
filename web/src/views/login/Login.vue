<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>HSK 博主观考后台</h1>
        <p>创建试卷，管理考试</p>
      </div>
      
      <el-form ref="formRef" :model="form" :rules="rules" class="login-form">
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <span>还没有账号？</span>
        <el-link type="primary" @click="showRegister = true">联系入驻</el-link>
      </div>
    </div>
    
    <!-- 注册对话框 -->
    <el-dialog v-model="showRegister" title="申请入驻" width="400px">
      <el-form :model="registerForm" label-width="80px">
        <el-form-item label="邮箱">
          <el-input v-model="registerForm.email" placeholder="你的邮箱" />
        </el-form-item>
        <el-form-item label="频道名">
          <el-input v-model="registerForm.youtube_channel_name" placeholder="YouTube频道名称" />
        </el-form-item>
        <el-form-item label="邀请码">
          <el-input v-model="registerForm.invite_code" placeholder="邀请码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" @click="handleRegister">申请入驻</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useCreatorStore } from '@/stores/creator'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const creatorStore = useCreatorStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const showRegister = ref(false)

const form = reactive({
  email: '',
  password: ''
})

const registerForm = reactive({
  email: '',
  youtube_channel_name: '',
  invite_code: ''
})

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

async function handleLogin() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await creatorStore.login(form.email, form.password)
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } catch (error) {
        console.error(error)
      } finally {
        loading.value = false
      }
    }
  })
}

async function handleRegister() {
  ElMessage.info('请等待平台审核，审核通过后会发送通知')
  showRegister.value = false
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
}

.login-header p {
  color: #999;
  font-size: 14px;
}

.login-form {
  margin-top: 20px;
}

.login-button {
  width: 100%;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  color: #999;
}
</style>
