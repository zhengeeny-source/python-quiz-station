<script setup>
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { addQuestion, readableApiError } from '../api/questions'

const formRef = ref()
const saving = ref(false)

const emptyForm = () => ({
  question_type: 'single_choice',
  title: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  answer: 'A',
  accepted_answers_text: '',
  analysis: '',
})

const form = reactive(emptyForm())
watch(
  () => form.question_type,
  (type) => {
    if (type !== 'single_choice') form.answer = 'A'
  },
)
const rules = {
  title: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  answer: [{ required: true, message: '请选择正确答案', trigger: 'change' }],
  analysis: [{ required: true, message: '请输入答案解析', trigger: 'blur' }],
}

async function saveQuestion() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  if (form.question_type === 'single_choice' && ![form.option_a, form.option_b, form.option_c, form.option_d].every((value) => value.trim())) {
    ElMessage.warning('选择题需要填写 A、B、C、D 四个选项')
    return
  }
  const acceptedAnswers = form.accepted_answers_text
    .split('\n')
    .map((value) => value.trim())
    .filter(Boolean)
  if (form.question_type === 'fill_blank' && !acceptedAnswers.length) {
    ElMessage.warning('填空题至少需要填写一个标准答案')
    return
  }

  saving.value = true
  try {
    const payload = { ...form, accepted_answers: form.question_type === 'fill_blank' ? acceptedAnswers : null }
    delete payload.accepted_answers_text
    if (form.question_type === 'true_false') {
      Object.assign(payload, { option_a: '正确', option_b: '错误', option_c: '', option_d: '' })
    }
    if (form.question_type === 'fill_blank') {
      Object.assign(payload, { option_a: '', option_b: '', option_c: '', option_d: '', answer: 'A' })
    }
    await addQuestion(payload)
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
        <el-form-item label="题型" prop="question_type">
          <el-radio-group v-model="form.question_type">
            <el-radio-button value="single_choice">选择题</el-radio-button>
            <el-radio-button value="true_false">判断题</el-radio-button>
            <el-radio-button value="fill_blank">填空题</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="题干" prop="title">
          <el-input
            v-model="form.title"
            type="textarea"
            :rows="7"
            placeholder="例如：下面代码输出什么？\n\n```python\ns = 'hello'\nprint(s.upper())\n```"
          />
        </el-form-item>

        <div v-if="form.question_type === 'single_choice'" class="option-form-grid">
          <el-form-item v-for="letter in ['a', 'b', 'c', 'd']" :key="letter" :label="`选项 ${letter.toUpperCase()}`" :prop="`option_${letter}`">
            <el-input v-model="form[`option_${letter}`]" :placeholder="`请输入 ${letter.toUpperCase()} 选项`" />
          </el-form-item>
        </div>

        <el-form-item v-if="form.question_type === 'single_choice'" label="正确答案" prop="answer">
          <el-radio-group v-model="form.answer">
            <el-radio-button v-for="letter in ['A', 'B', 'C', 'D']" :key="letter" :value="letter">
              {{ letter }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-else-if="form.question_type === 'true_false'" label="正确答案" prop="answer">
          <el-radio-group v-model="form.answer">
            <el-radio-button value="A">正确</el-radio-button>
            <el-radio-button value="B">错误</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-else label="标准答案（每行一个等价答案）" prop="accepted_answers_text">
          <el-input
            v-model="form.accepted_answers_text"
            type="textarea"
            :rows="4"
            placeholder="例如：Python is powerful"
          />
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
