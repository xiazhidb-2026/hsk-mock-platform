<template>
  <div class="question-types-config">
    <h3>题型配置说明</h3>
    <el-table :data="questionTypeConfigs" stripe>
      <el-table-column prop="section" label="考试部分" width="100">
        <template #default="{ row }">
          <el-tag :type="getSectionType(row.section)">{{ row.section }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="type" label="题型" />
      <el-table-column prop="description" label="说明" />
      <el-table-column prop="score" label="分值" width="80" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
const questionTypeConfigs = [
  { section: '听力', type: 'listen_choose_picture', description: '看图片，听问题，选答案', score: 2 },
  { section: '听力', type: 'listen_dialogue', description: '听对话，选答案', score: 2 },
  { section: '听力', type: 'listen_passage', description: '听短文，选答案', score: 2 },
  { section: '阅读', type: 'reading_choose_word', description: '选词填空', score: 2 },
  { section: '阅读', type: 'reading_cloze', description: '完形填空', score: 2 },
  { section: '阅读', type: 'reading_understand', description: '阅读理解', score: 2 },
  { section: '阅读', type: 'reading_sentence_order', description: '句子排序', score: 2 },
  { section: '阅读', type: 'reading_true_false', description: '判断对错', score: 2 },
  { section: '书写', type: 'writing_phrase', description: '组词成句', score: 10 },
  { section: '书写', type: 'writing_essay', description: '短文写作', score: 20 }
]

function getSectionType(section: string) {
  const map: Record<string, string> = {
    '听力': 'primary',
    '阅读': 'success',
    '书写': 'warning'
  }
  return map[section] || 'info'
}
</script>

<style scoped>
.question-types-config {
  margin-top: 20px;
}

h3 {
  margin-bottom: 15px;
}
</style>
