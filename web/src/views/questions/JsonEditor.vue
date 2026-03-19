<template>
  <div class="json-editor">
    <el-input
      v-model="jsonString"
      type="textarea"
      :rows="10"
      placeholder='{"key": "value"}'
      @blur="handleBlur"
    />
    <div v-if="parseError" class="error">{{ parseError }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: object | null
}>()

const emit = defineEmits(['update:modelValue'])

const jsonString = ref('')
const parseError = ref('')

watch(() => props.modelValue, (val) => {
  if (val) {
    jsonString.value = JSON.stringify(val, null, 2)
  }
}, { immediate: true })

function handleBlur() {
  try {
    const parsed = JSON.parse(jsonString.value)
    emit('update:modelValue', parsed)
    parseError.value = ''
  } catch (e: any) {
    parseError.value = 'JSON格式错误: ' + e.message
  }
}
</script>

<style scoped>
.json-editor {
  width: 100%;
}

.error {
  color: #F56C6C;
  font-size: 12px;
  margin-top: 5px;
}
</style>
