<template>
  <div class="question-list">
    <!-- 筛选和操作栏 -->
    <el-card>
      <div class="toolbar">
        <div class="filters">
          <el-select v-model="filters.level" placeholder="HSK等级" clearable style="width: 120px">
            <el-option label="HSK 4级" :value="4" />
            <el-option label="HSK 5级" :value="5" />
          </el-select>
          <el-select v-model="filters.section" placeholder="题型" clearable style="width: 120px">
            <el-option label="听力" value="listening" />
            <el-option label="阅读" value="reading" />
            <el-option label="书写" value="writing" />
          </el-select>
          <el-button @click="loadQuestions">筛选</el-button>
        </div>
        <div class="actions">
          <el-button type="primary" @click="$router.push('/questions/create')">
            <el-icon><Plus /></el-icon>
            创建题目
          </el-button>
          <el-button @click="showImport = true">
            <el-icon><Upload /></el-icon>
            批量导入
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 题目列表 -->
    <el-card style="margin-top: 20px">
      <el-table :data="questions" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="220">
          <template #default="{ row }">
            {{ row.id?.slice(0, 8) }}...
          </template>
        </el-table-column>
        <el-table-column prop="hsk_level" label="等级" width="80">
          <template #default="{ row }">
            <el-tag>HSK{{ row.hsk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="section" label="部分" width="80">
          <template #default="{ row }">
            <el-tag :type="getSectionType(row.section)">
              {{ getSectionName(row.section) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question_type" label="题型" />
        <el-table-column prop="difficulty" label="难度" width="80">
          <template #default="{ row }">
            <el-rate v-model="row.difficulty" disabled :max="5" />
          </template>
        </el-table-column>
        <el-table-column prop="usage_count" label="使用次数" width="100" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @change="loadQuestions"
        />
      </div>
    </el-card>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="showImport" title="批量导入题目" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".xlsx,.xls"
        :limit="1"
      >
        <el-button type="primary">选择Excel文件</el-button>
        <template #tip>
          <div class="upload-tip">
            请下载
            <el-link type="primary" :underline="false" @click="downloadTemplate">导入模板</el-link>
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showImport = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'
import { questionAPI } from '@/api'

const router = useRouter()

const loading = ref(false)
const questions = ref<any[]>([])
const showImport = ref(false)
const importing = ref(false)
const uploadRef = ref()

const filters = reactive({
  level: null as number | null,
  section: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

let importFile: File | null = null

onMounted(() => {
  loadQuestions()
})

async function loadQuestions() {
  loading.value = true
  try {
    const res: any = await questionAPI.list({
      level: filters.level,
      section: filters.section,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    questions.value = res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function getSectionName(section: string) {
  const map: Record<string, string> = {
    listening: '听力',
    reading: '阅读',
    writing: '书写'
  }
  return map[section] || section
}

function getSectionType(section: string) {
  const map: Record<string, string> = {
    listening: 'primary',
    reading: 'success',
    writing: 'warning'
  }
  return map[section] || 'info'
}

function handleEdit(row: any) {
  router.push(`/questions/create?id=${row.id}`)
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定要删除这道题目吗？', '提示', {
    type: 'warning'
  })
  try {
    await questionAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadQuestions()
  } catch (error) {
    console.error(error)
  }
}

function handleFileChange(file: UploadFile) {
  importFile = file.raw || null
}

function downloadTemplate() {
  ElMessage.info('模板下载功能开发中')
}

async function handleImport() {
  if (!importFile) {
    ElMessage.warning('请选择文件')
    return
  }
  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', importFile)
    await questionAPI.import(formData)
    ElMessage.success('导入成功')
    showImport.value = false
    loadQuestions()
  } catch (error) {
    console.error(error)
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  gap: 10px;
}

.actions {
  display: flex;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.upload-tip {
  margin-top: 10px;
  color: #999;
}
</style>
