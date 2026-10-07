<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { addQuestion, readableApiError } from '../api/questions'

const formRef = ref()
const saving = ref(false)

const emptyForm = () => ({
  title: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  answer: 'A',
  analysis: '',
})

const form = reactive(emptyForm())
const rules = {
  title: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  option_a: [{ required: true, message: '请输入 A 选项', trigger: 'blur' }],
  option_b: [{ required: true, message: '请输入 B 选项', trigger: 'blur' }],
  option_c: [{ required: true, message: '请输入 C 选项', trigger: 'blur' }],
  option_d: [{ required: true, message: '请输入 D 选项', trigger: 'blur' }],
  answer: [{ required: true, message: '请选择正确答案', trigger: 'change' }],
  analysis: [{ required: true, message: '请输入答案解析', trigger: 'blur' }],
}

async function saveQuestion() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    await addQuestion(form)
    ElMessage.success('题目已保存到题库')
    Object.assign(form, emptyForm())
    formRef.value.clearValidate()
  } catch (error) {
    ElMessage.error(readableApiError(error, '保存失败，请稍后重试'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="add-page">
    <div class="page-heading compact">
      <div>
        <span class="eyebrow">QUESTION MANAGER</span>
        <h1>新增一道题目</h1>
        <p>无需登录，保存后题目会直接进入当前数据库。</p>
      </div>
    </div>

    <el-alert
      title="题干和解析支持 Markdown；Python 代码请放在 ```python 与 ``` 之间。"
      type="info"
      :closable="false"
      show-icon
    />

    <el-card class="form-card" shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
        <el-form-item label="题干" prop="title">
          <el-input
            v-model="form.title"
            type="textarea"
            :rows="7"
            placeholder="例如：下面代码输出什么？\n\n```python\ns = 'hello'\nprint(s.upper())\n```"
          />
        </el-form-item>

        <div class="option-form-grid">
          <el-form-item v-for="letter in ['a', 'b', 'c', 'd']" :key="letter" :label="`选项 ${letter.toUpperCase()}`" :prop="`option_${letter}`">
            <el-input v-model="form[`option_${letter}`]" :placeholder="`请输入 ${letter.toUpperCase()} 选项`" />
          </el-form-item>
        </div>

        <el-form-item label="正确答案" prop="answer">
          <el-radio-group v-model="form.answer">
            <el-radio-button v-for="letter in ['A', 'B', 'C', 'D']" :key="letter" :value="letter">
              {{ letter }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="答案解析" prop="analysis">
          <el-input v-model="form.analysis" type="textarea" :rows="5" placeholder="说明为什么该选项正确，以及容易混淆的知识点。" />
        </el-form-item>

        <el-button type="primary" :loading="saving" @click="saveQuestion">保存题目</el-button>
        <el-button @click="Object.assign(form, emptyForm())">清空</el-button>
      </el-form>
    </el-card>
  </section>
</template>

