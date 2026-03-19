<template>
  <div class="analytics">
    <!-- 时间筛选 -->
    <el-card>
      <div class="toolbar">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="loadData"
        />
        <el-button @click="setQuickDate(7)">近7天</el-button>
        <el-button @click="setQuickDate(30)">近30天</el-button>
        <el-button @click="setQuickDate(90)">近90天</el-button>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">考试次数</div>
            <div class="stat-value">{{ stats.total_exams || 0 }}</div>
            <div class="stat-change" :class="stats.exams_change > 0 ? 'up' : 'down'">
              {{ stats.exams_change > 0 ? '+' : '' }}{{ stats.exams_change || 0 }}%
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">参考人数</div>
            <div class="stat-value">{{ stats.total_users || 0 }}</div>
            <div class="stat-change" :class="stats.users_change > 0 ? 'up' : 'down'">
              {{ stats.users_change > 0 ? '+' : '' }}{{ stats.users_change || 0 }}%
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">平均分</div>
            <div class="stat-value">{{ stats.avg_score || 0 }}</div>
            <div class="stat-change up">+5.2%</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">通过率</div>
            <div class="stat-value">{{ stats.pass_rate || 0 }}%</div>
            <div class="stat-change up">+3.1%</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表 -->
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
              <span>题型分布</span>
            </div>
          </template>
          <div ref="pieChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细表格 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>试卷热度排行</span>
            </div>
          </template>
          <el-table :data="templateRanking" stripe>
            <el-table-column type="rank" label="排名" width="60">
              <template #default="{ $index }">
                {{ $index + 1 }}
              </template>
            </el-table-column>
            <el-table-column prop="name" label="试卷名称" />
            <el-table-column prop="hsk_level" label="等级" width="80">
              <template #default="{ row }">
                HSK{{ row.hsk_level }}
              </template>
            </el-table-column>
            <el-table-column prop="exam_count" label="考试次数" width="100" />
            <el-table-column prop="avg_score" label="平均分" width="100" />
            <el-table-column prop="pass_rate" label="通过率" width="100">
              <template #default="{ row }">
                {{ row.pass_rate }}%
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import dayjs from 'dayjs'

const dateRange = ref<[Date, Date]>([
  dayjs().subtract(30, 'day').toDate(),
  dayjs().toDate()
])

const stats = ref<any>({
  total_exams: 0,
  total_users: 0,
  avg_score: 0,
  pass_rate: 0,
  exams_change: 0,
  users_change: 0
})

const templateRanking = ref<any[]>([])

const trendChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
let trendChart: ECharts | null = null
let pieChart: ECharts | null = null

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  trendChart?.dispose()
  pieChart?.dispose()
})

function setQuickDate(days: number) {
  dateRange.value = [
    dayjs().subtract(days, 'day').toDate(),
    dayjs().toDate()
  ]
  loadData()
}

async function loadData() {
  // 模拟数据
  stats.value = {
    total_exams: 1256,
    total_users: 892,
    avg_score: 215,
    pass_rate: 72,
    exams_change: 15.3,
    users_change: 8.7
  }

  templateRanking.value = [
    { name: 'HSK4级全真模拟卷01', hsk_level: 4, exam_count: 456, avg_score: 218, pass_rate: 75 },
    { name: 'HSK5级冲刺卷', hsk_level: 5, exam_count: 312, avg_score: 195, pass_rate: 62 },
    { name: 'HSK4级听力专项', hsk_level: 4, exam_count: 234, avg_score: 225, pass_rate: 78 },
    { name: 'HSK5级阅读强化', hsk_level: 5, exam_count: 156, avg_score: 188, pass_rate: 58 },
    { name: 'HSK4级模拟考试', hsk_level: 4, exam_count: 98, avg_score: 232, pass_rate: 82 }
  ]

  initCharts()
}

function initCharts() {
  // 趋势图
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['考试次数', '参考人数'] },
      xAxis: {
        type: 'category',
        data: Array.from({ length: 7 }, (_, i) => dayjs().subtract(6 - i, 'day').format('MM-DD'))
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '考试次数',
          type: 'line',
          data: [120, 132, 101, 134, 90, 230, 210],
          smooth: true,
          areaStyle: { color: 'rgba(64, 158, 255, 0.2)' }
        },
        {
          name: '参考人数',
          type: 'line',
          data: [85, 98, 76, 89, 65, 156, 142],
          smooth: true,
          areaStyle: { color: 'rgba(103, 194, 58, 0.2)' }
        }
      ]
    })
  }

  // 饼图
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          data: [
            { value: 45, name: '听力', itemStyle: { color: '#409EFF' } },
            { value: 40, name: '阅读', itemStyle: { color: '#67C23A' } },
            { value: 15, name: '书写', itemStyle: { color: '#E6A23C' } }
          ]
        }
      ]
    })
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px;
}

.stat-label {
  color: #999;
  font-size: 14px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #333;
  margin: 10px 0;
}

.stat-change {
  font-size: 14px;
}

.stat-change.up {
  color: #67C23A;
}

.stat-change.down {
  color: #F56C6C;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
