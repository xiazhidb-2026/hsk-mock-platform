<template>
  <div class="settings">
    <el-card>
      <template #header>
        <span>个人设置</span>
      </template>
      
      <el-form label-width="120px">
        <el-form-item label="邮箱">
          <el-input v-model="userInfo.email" disabled />
        </el-form-item>
        
        <el-form-item label="频道名称">
          <el-input v-model="userInfo.youtube_channel_name" />
        </el-form-item>
        
        <el-form-item label="头像">
          <el-avatar :size="80" :src="userInfo.avatar_url">
            {{ userInfo.youtube_channel_name?.slice(0, 1) }}
          </el-avatar>
        </el-form-item>
        
        <el-form-item label="邀请码">
          <el-input v-model="userInfo.invite_code" disabled>
            <template #append>
              <el-button @click="copyInviteCode">复制</el-button>
            </template>
          </el-input>
          <div class="form-tip">分享给其他博主使用</div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSave">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px">
      <template #header>
        <span>修改密码</span>
      </template>
      
      <el-form label-width="120px">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="确认密码">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useCreatorStore } from '@/stores/creator'

const creatorStore = useCreatorStore()

const userInfo = reactive({
  email: '',
  youtube_channel_name: '',
  avatar_url: '',
  invite_code: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

onMounted(() => {
  if (creatorStore.user) {
    userInfo.email = creatorStore.user.email
    userInfo.youtube_channel_name = creatorStore.user.youtube_channel_name || ''
    userInfo.avatar_url = creatorStore.user.avatar_url || ''
  }
})

function copyInviteCode() {
  if (userInfo.invite_code) {
    navigator.clipboard.writeText(userInfo.invite_code)
    ElMessage.success('邀请码已复制')
  }
}

function handleSave() {
  ElMessage.success('保存成功')
}

function handleChangePassword() {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次密码输入不一致')
    return
  }
  ElMessage.success('密码修改成功')
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
}
</script>

<style scoped>
.settings {
  max-width: 600px;
}

.form-tip {
  color: #999;
  font-size: 12px;
  margin-top: 5px;
}
</style>
