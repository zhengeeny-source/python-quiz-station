<template>
  <view class="page-shell">
    <view class="hero">
      <text class="eyebrow">QUESTION MANAGER</text>
      <text class="page-title">新增一道题目</text>
      <text class="page-subtitle">保存后会直接进入与网站共用的题库。</text>
    </view>

    <view class="card form-card">
      <view class="form-field">
        <text class="field-label">题型</text>
        <view class="pill-row">
          <view
            v-for="item in questionTypes"
            :key="item.value"
            class="pill"
            :class="{ active: form.question_type === item.value }"
            @click="setQuestionType(item.value)"
          >{{ item.label }}</view>
        </view>
      </view>

      <view class="form-field">
        <text class="field-label">题干</text>
        <textarea v-model="form.title" class="text-area title-area" placeholder="支持 Markdown；Python 代码放在 ```python 与 ``` 之间" />
      </view>

      <template v-if="form.question_type === 'single_choice'">
        <view v-for="letter in letters" :key="letter" class="form-field">
          <text class="field-label">选项 {{ letter }}</text>
          <input v-model="form[`option_${letter.toLowerCase()}`]" class="text-input" :placeholder="`请输入 ${letter} 选项`" />
        </view>
        <view class="form-field">
          <text class="field-label">正确答案</text>
          <view class="pill-row">
            <view v-for="letter in letters" :key="letter" class="pill" :class="{ active: form.answer === letter }" @click="form.answer = letter">{{ letter }}</view>
          </view>
        </view>
      </template>

      <view v-else-if="form.question_type === 'true_false'" class="form-field">
        <text class="field-label">正确答案</text>
        <view class="pill-row">
          <view class="pill" :class="{ active: form.answer === 'A' }" @click="form.answer = 'A'">正确</view>
          <view class="pill" :class="{ active: form.answer === 'B' }" @click="form.answer = 'B'">错误</view>
        </view>
      </view>

      <view v-else class="form-field">
        <text class="field-label">标准答案（每行一个等价答案）</text>
        <textarea v-model="form.accepted_answers_text" class="text-area" placeholder="例如：Python is powerful" />
      </view>

      <view class="form-field">
        <text class="field-label">答案解析</text>
        <textarea v-model="form.analysis" class="text-area" placeholder="说明正确原因与容易混淆的知识点" />
      </view>

      <button class="primary-button" :loading="saving" :disabled="saving" @click="saveQuestion">保存题目</button>
      <button class="secondary-button clear-button" @click="resetForm">清空</button>
    </view>
  </view>
</template>

<script>
import { addQuestion, readableApiError } from '../../api/client'

function emptyForm() {
  return {
    question_type: 'single_choice',
    title: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    answer: 'A',
    accepted_answers_text: '',
    analysis: '',
  }
}

export default {
  data() {
    return {
      saving: false,
      letters: ['A', 'B', 'C', 'D'],
      questionTypes: [
        { value: 'single_choice', label: '选择题' },
        { value: 'true_false', label: '判断题' },
        { value: 'fill_blank', label: '填空题' },
      ],
      form: emptyForm(),
    }
  },
  methods: {
    setQuestionType(type) {
      this.form.question_type = type
      if (type !== 'single_choice') this.form.answer = 'A'
    },
    resetForm() {
      this.form = emptyForm()
    },
    async saveQuestion() {
      if (!this.form.title.trim() || !this.form.analysis.trim()) {
        uni.showToast({ title: '请填写题干和答案解析', icon: 'none' })
        return
      }
      if (
        this.form.question_type === 'single_choice'
        && ![this.form.option_a, this.form.option_b, this.form.option_c, this.form.option_d].every((value) => value.trim())
      ) {
        uni.showToast({ title: '选择题需要填写四个选项', icon: 'none' })
        return
      }
      const acceptedAnswers = this.form.accepted_answers_text
        .split('\n')
        .map((value) => value.trim())
        .filter(Boolean)
      if (this.form.question_type === 'fill_blank' && !acceptedAnswers.length) {
        uni.showToast({ title: '填空题至少需要一个标准答案', icon: 'none' })
        return
      }

      const payload = {
        ...this.form,
        accepted_answers: this.form.question_type === 'fill_blank' ? acceptedAnswers : null,
      }
      delete payload.accepted_answers_text
      if (this.form.question_type === 'true_false') {
        Object.assign(payload, { option_a: '正确', option_b: '错误', option_c: '', option_d: '' })
      }
      if (this.form.question_type === 'fill_blank') {
        Object.assign(payload, { option_a: '', option_b: '', option_c: '', option_d: '', answer: 'A' })
      }

      this.saving = true
      try {
        await addQuestion(payload)
        uni.showToast({ title: '题目已保存', icon: 'success' })
        this.resetForm()
      } catch (error) {
        uni.showToast({ title: readableApiError(error, '保存失败，请稍后重试'), icon: 'none' })
      } finally {
        this.saving = false
      }
    },
  },
}
</script>

<style scoped>
.title-area {
  min-height: 280rpx;
}

.clear-button {
  margin-top: 16rpx;
}
</style>
