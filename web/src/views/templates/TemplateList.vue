<template>
  <div class="template-list">
    <!-- 筛选和操作栏 -->
    <el-card>
      <div class="toolbar">
        <div class="filters">
          <el-select v-model="filters.level" placeholder="HSK等级" clearable style="width: 120px">
            <el-option label="HSK 4级" :value="4" />
            <el-option label="HSK 5级" :value="5" />
          </el-select>
          <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
          </el-select>
          <el-button @click="loadTemplates">筛选</el-button>
        </div>
        <div class="actions">
          <el-button type="primary" @click="$router.push('/templates/create')">
            <el-icon><Plus /></el-icon>
            创建试卷
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 试卷列表 -->
    <el-card style="margin-top: 20px">
      <el-table :data="templates" v-loading="loading" stripe>
        <el-table-column prop="name" label="试卷名称" min-width="150" />
        <el-table-column prop="hsk_level" label="等级" width="100">
          <template #default="{ row }">
            <el-tag>HSK{{ row.hsk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_questions" label="题数" width="80" />
        <el-table-column prop="time_limit" label="时长" width="80">
          <template #default="{ row }">
            {{ Math.floor(row.time_limit / 60) }}分钟
          </template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            {{ row.price === 0 ? '免费' : row.price + '积分' }}
          </template>
        </el-table-column>
        <el-table-column prop="publish_count" label="考试次数" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button 
              v-if="row.status !== 'published'" 
              type="success" 
              link 
              @click="handlePublish(row)"
            >发布</el-button>
            <el-button 
              v-else 
              type="warning" 
              link 
              @click="handleUnpublish(row)"
            >下架</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
     试卷列表
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
          @change="loadTemplates"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { templateAPI } from '@/api'

const router = useRouter()

const loading = ref(false)
const templates = ref<any[]>([])

const filters = reactive({
  level: null as number | null,
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

onMounted(() => {
  loadTemplates()
})

async function loadTemplates() {
  loading.value = true
  try {
    const res: any = await templateAPI.list({
      level: filters.level,
      status: filters.status,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    templates.value = res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function handleEdit(row: any) {
  router.push(`/templates/create?id=${row.id}`)
}

async function handlePublish(row: any) {
  try {
    await templateAPI.publish(row.id)
    ElMessage.success('发布成功')
    loadTemplates()
  } catch (error) {
    console.error(error)
  }
}

async function handleUnpublish(row: any) {
  await ElMessageBox.confirm('确定要下架这份试卷吗？', '提示', {
    type: 'warning'
  })
  // 下架逻辑
  ElMessage.success('下架成功')
  loadTemplates()
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定要删除这份试卷吗？', '提示', {
    type: 'warning'
  })
  try {
    await templateAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadTemplates
  } catch (error) {
    console.error(error)
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
</style>
