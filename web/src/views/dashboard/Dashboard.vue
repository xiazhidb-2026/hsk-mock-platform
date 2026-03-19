<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #409EFF">
            <el-icon :size="30"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_exams || 0 }}</div>
            <div class="stat-label">考试次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #67C23A">
            <el-icon :size="30"><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_users || 0 }}</div>
            <div class="stat-label">用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #E6A23C">
            <el-icon :size="30"><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.avg_score || 0 }}</div>
            <div class="stat-label">平均分</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #F56C6C">
            <el-icon :size="30"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pass_rate || 0 }}%</div>
            <div class="stat-label">通过率</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>考试趋势</span>
            </div>
          </template>
          <div ref="trendChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>热门试卷</span>
            </div>
          </template>
          <div class="popular-list">
            <div v-for="(item, index) in popularTemplates" :key="index" class="popular-item">
              <span class="rank">{{ index + 1 }}</span>
              <span class="name">{{ item.name }}</span>
              <span class="count">{{ item.count }}次</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近考试 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近考试记录</span>
            </div>
          </template>
          <el-table :data="recentExams" stripe>
            <el-table-column prop="device_uuid" label="用户" width="150">
              <template #default="{ row }">
                {{ row.device_uuid?.slice(0, 8) }}...
              </template>
            </el-table-column>
            <el-table-column prop="template_name" label="试卷" />
            <el-table-column prop="total_score" label="分数" width="100" />
            <el-table-column prop="level_result" label="等级" width="100" />
            <el-table-column prop="completed_at" label="考试时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { Document, User, TrendCharts, CircleCheck } from '@element-plus/icons-vue'
import { statsAPI } from '@/api'

const stats = ref<any>({})
const popularTemplates = ref<any[]>([])
const recentExams = ref<any[]>([])
const trendChartRef = ref<HTMLElement>()
let trendChart: ECharts | null = null

onMounted(async () => {
  try {
    const res: any = await statsAPI.getDashboard()
    stats.value = res.data || res
    popularTemplates.value = stats.value.popular_templates || []
    recentExams.value = stats.value.recent_exams || []
    initChart()
  } catch (error) {
    console.error(error)
  }
})

function initChart() {
  if (!trendChartRef.value) return
  
  trendChart = echarts.init(trendChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '考试次数',
        type: 'line',
        data: [120, 132, 101, 134, 90, 230, 210],
        smooth: true,
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.2)'
        }
      }
    ]
  }
  
  trendChart.setOption(option)
}
</script>

<style scoped>
.stats-row {
  margin-top: 10px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-right: 15px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.popular-list {
  max-height: 300px;
  overflow-y: auto;
}

.popular-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.popular-item .rank {
  width: 24px;
  height: 24px;
  background: #409EFF;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  margin-right: 10px;
}

.popular-item .name {
  flex: 1;
  font-size: 14px;
}

.popular-item .count {
  color: #999;
  font-size: 12px;
}
</style>
