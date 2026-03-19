<template>
  <div class="question-create">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑题目' : '创建题目' }}</span>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <!-- 基本信息 -->
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="HSK等级" prop="hsk_level">
              <el-select v-model="form.hsk_level" placeholder="选择等级">
                <el-option label="HSK 4级" :value="4" />
                <el-option label="HSK 5级" :value="5" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="考试部分" prop="section">
              <el-select v-model="form.section" placeholder="选择部分">
                <el-option label="听力" value="listening" />
                <el-option label="阅读" value="reading" />
                <el-option label="书写" value="writing" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="题型" prop="question_type">
              <el-select v-model="form.question_type" placeholder="选择题型">
                <el-option-group v-for="group in questionTypes" :key="group.label" :label="group.label">
                  <el-option
                    v-for="item in group.options"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 难度 -->
        <el-form-item label="难度" prop="difficulty">
          <el-rate v-model="form.difficulty" :max="5" show-text :texts="['很简单', '简单', '中等', '较难', '很难']" />
        </el-form-item>
        
        <!-- 听力音频 -->
        <el-form-item v-if="form.section === 'listening'" label="听力音频">
          <el-upload
            :auto-upload="false"
            :on-change="handleAudioChange"
            accept=".mp3,.m4a,.wav"
            :limit="1"
          >
            <el-button>上传音频</el-button>
            <template #tip>
              <div class="upload-tip">支持 MP3、M4A、WAV 格式</div>
            </template>
          </el-upload>
        </el-form-item>
        
        <!-- 题目内容 -->
        <el-form-item label="题目内容" prop="content">
          <JsonEditor v-model="form.content" />
        </el-form-item>
        
        <!-- 选项 -->
        <el-form-item label="选项" v-if="hasOptions">
          <div v-for="(option, index) in form.options" :key="index" class="option-item">
            <el-radio v-model="form.correct_answer.answer" :label="option.id">
              <el-input v-model="option.text" placeholder="选项内容" />
            </el-radio>
            <el-button type="danger" link @click="removeOption(index)">删除</el-button>
          </div>
          <el-button type="primary" link @click="addOption">添加选项</el-button>
        </el-form-item>
        
        <!-- 正确答案 -->
        <el-form-item label="正确答案" prop="correct_answer">
          <el-input v-model="form.correct_answer.answer" placeholder="正确答案" />
        </el-form-item>
        
        <!-- 解析 -->
        <el-form-item label="解析">
          <el-input v-model="form.explanation" type="textarea" :rows="3" placeholder="题目解析" />
        </el-form-item>
        
        <!-- 标签 -->
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple placeholder="选择标签" allow-create filterable>
            <el-option label="语法" value="grammar" />
            <el-option label="词汇" value="vocabulary" />
            <el-option label="听力" value="listening" />
            <el-option label="阅读" value="reading" />
          </el-select>
        </el-form-item>
        
        <!-- 提交 -->
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '创建题目' }}
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import JsonEditor from './JsonEditor.vue'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const saving = ref(false)
const isEdit = ref(false)
const questionId = ref('')

const form = reactive({
  hsk_level: 4,
  section: 'listening',
  question_type: '',
  difficulty: 3,
  content: {} as any,
  options: [] as any[],
  correct_answer: { answer: '' },
  explanation: '',
  tags: [] as string[],
  audio_url: ''
})

const rules: FormRules = {
  hsk_level: [{ required: true, message: '请选择HSK等级', trigger: 'change' }],
  section: [{ required: true, message: '请选择考试部分', trigger: 'change' }],
  question_type: [{ required: true, message: '请选择题型', trigger: 'change' }]
}

const questionTypes = [
  {
    label: '听力',
    options: [
      { label: '看图选答案', value: 'listen_choose_picture' },
      { label: '对话选择', value: 'listen_dialogue' },
      { label: '短文理解', value: 'listen_passage' }
    ]
  },
  {
    label: '阅读',
    options: [
      { label: '选词填空', value: 'reading_choose_word' },
      { label: '完形填空', value: 'reading_cloze' },
      { label: '阅读理解', value: 'reading_understand' },
      { label: '句子排序', value: 'reading_sentence_order' }
    ]
  },
  {
    label: '书写',
    options: [
      { label: '组词成句', value: 'writing_phrase' },
      { label: '短文写作', value: 'writing_essay' }
    ]
  }
]

const hasOptions = computed(() => {
  return form.section !== 'writing' || form.question_type === 'writing_phrase'
})

onMounted(() => {
  if (route.query.id) {
    isEdit.value = true
    questionId.value = route.query.id as string
    loadQuestion()
  }
  // 默认添加4个选项
  form.options = [
    { id: 'A', text: '' },
    { id: 'B', text: '' },
    { id: 'C', text: '' },
    { id: 'D', text: '' }
  ]
})

async function loadQuestion() {
  // 加载题目详情
}

function handleAudioChange(file: any) {
  form.audio_url = URL.createObjectURL(file.raw)
}

function addOption() {
  const id = String.fromCharCode(65 + form.options.length)
  form.options.push({ id, text: '' })
}

function removeOption(index: number) {
  form.options.splice(index, 1)
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        const data = {
          ...form,
          options: form.options.filter(o => o.text)
        }
        
        if (isEdit.value) {
          // 更新
          ElMessage.success('保存成功')
        } else {
          // 创建
          ElMessage.success('创建成功')
        }
        router.push('/questions')
      } catch (error) {
        console.error(error)
      } finally {
        saving.value = false
      }
    }
  })
}

function handleCancel() {
  router.back()
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.upload-tip {
  color: #999;
  font-size: 12px;
  margin-top: 5px;
}
</style>
