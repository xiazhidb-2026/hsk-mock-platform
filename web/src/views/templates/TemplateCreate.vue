<template>
  <div class="template-create">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑试卷' : '创建试卷' }}</span>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <!-- 基本信息 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="试卷名称" prop="name">
              <el-input v-model="form.name" placeholder="例如：HSK4级全真模拟卷01" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="HSK等级" prop="hsk_level">
              <el-select v-model="form.hsk_level" placeholder="选择等级">
                <el-option label="HSK 4级" :value="4" />
                <el-option label="HSK 5级" :value="5" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="价格" prop="price">
              <el-input-number v-model="form.price" :min="0" :max="100" />
              <span style="margin-left: 10px">积分 (0=免费)</span>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 描述 -->
        <el-form-item label="试卷描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述这份试卷的特点" />
        </el-form-item>
        
        <!-- 时间限制 -->
        <el-form-item label="时间限制" prop="time_limit">
          <el-input-number v-model="form.time_limit" :min="600" :max="7200" :step="300" />
          <span style="margin-left: 10px">秒 (建议: HSK4级=3600秒, HSK5级=4500秒)</span>
        </el-form-item>
        
        <!-- 题型配置 -->
        <el-divider>题型配置</el-divider>
        
        <div class="section-config">
          <div v-for="section in sections" :key="section.name" class="section-block">
            <div class="section-header">
              <h3>{{ section.label }}</h3>
              <span class="section-info">
                已选: {{ getSectionQuestionCount(section.name) }}题
              </span>
            </div>
            
            <div v-for="qtype in section.types" :key="qtype.value" class="question-type-row">
              <span class="qtype-label">{{ qtype.label }}</span>
              <el-input-number 
                v-model="form.structure.sections[section.name].question_types[qtype.value]" 
                :min="0" 
                :max="50"
                size="small"
              />
              <span class="qtype-score">× {{ qtype.score }}分 = {{ (form.structure.sections[section.name].question_types[qtype.value] || 0) * qtype.score }}分</span>
            </div>
          </div>
        </div>
        
        <!-- 统计 -->
        <el-divider />
        <div class="summary">
          <div class="summary-item">
            <span class="label">总题数：</span>
            <span class="value">{{ totalQuestions }}题</span>
          </div>
          <div class="summary-item">
            <span class="label">总分：</span>
            <span class="value">{{ totalScore }}分</span>
          </div>
          <div class="summary-item">
            <span class="label">预计时长：</span>
            <span class="value">{{ Math.floor(form.time_limit / 60) }}分钟</span>
          </div>
        </div>
        
        <!-- 提交 -->
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '创建试卷' }}
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

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const saving = ref(false)
const isEdit = ref(false)
const templateId = ref('')

const form = reactive({
  name: '',
  hsk_level: 4,
  description: '',
  time_limit: 3600,
  price: 0,
  structure: {
    sections: {
      listening: {
        question_types: {} as Record<string, number>
      },
      reading: {
        question_types: {} as Record<string, number>
      },
      writing: {
        question_types: {} as Record<string, number>
      }
    }
  } as any
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入试卷名称', trigger: 'blur' }],
  hsk_level: [{ required: true, message: '请选择HSK等级', trigger: 'change' }],
  time_limit: [{ required: true, message: '请设置时间限制', trigger: 'blur' }]
}

const sections = [
  {
    name: 'listening',
    label: '听力',
    types: [
      { label: '看图选答案', value: 'listen_choose_picture', score: 2 },
      { label: '对话选择', value: 'listen_dialogue', score: 2 },
      { label: '短文理解', value: 'listen_passage', score: 2 }
    ]
  },
  {
    name: 'reading',
    label: '阅读',
    types: [
      { label: '选词填空', value: 'reading_choose_word', score: 2 },
      { label: '完形填空', value: 'reading_cloze', score: 2 },
      { label: '阅读理解', value: 'reading_understand', score: 2 },
      { label: '句子排序', value: 'reading_sentence_order', score: 2 }
    ]
  },
  {
    name: 'writing',
    label: '书写',
    types: [
      { label: '组词成句', value: 'writing_phrase', score: 10 },
      { label: '短文写作', value: 'writing_essay', score: 20 }
    ]
  }
]

const totalQuestions = computed(() => {
  let total = 0
  for (const section of Object.values(form.structure.sections) as any[]) {
    for (const count of Object.values(section.question_types) as number[]) {
      total += count
    }
  }
  return total
})

const totalScore = computed(() => {
  let total = 0
  for (const section of sections) {
    const sectionData = form.structure.sections[section.name]
    for (const qtype of section.types) {
      const count = sectionData.question_types[qtype.value] || 0
      total += count * qtype.score
    }
  }
  return total
})

onMounted(() => {
  if (route.query.id) {
    isEdit.value = true
    templateId.value = route.query.id as string
    loadTemplate()
  }
})

async function loadTemplate() {
  // 加载试卷详情
}

function getSectionQuestionCount(sectionName: string): number {
  const section = form.structure.sections[sectionName]
  return Object.values(section.question_types).reduce((a: any, b: any) => a + b, 0)
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      if (totalQuestions.value === 0) {
        ElMessage.warning('请至少选择一道题目')
        return
      }
      
      saving.value = true
      try {
        const data = {
          ...form,
          total_questions: totalQuestions.value,
          total_score: totalScore.value
        }
        
        if (isEdit.value) {
          ElMessage.success('保存成功')
        } else {
          ElMessage.success('创建成功')
        }
        router.push('/templates')
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

.section-config {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-block {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h3 {
  margin: 0;
  color: #409EFF;
}

.section-info {
  color: #999;
  font-size: 14px;
}

.question-type-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.qtype-label {
  width: 120px;
}

.qtype-score {
  color: #999;
  font-size: 14px;
}

.summary {
  display: flex;
  gap: 40px;
  justify-content: center;
}

.summary-item {
  display: flex;
  gap: 10px;
}

.summary-item .label {
  color: #999;
}

.summary-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #409EFF;
}
</style>
