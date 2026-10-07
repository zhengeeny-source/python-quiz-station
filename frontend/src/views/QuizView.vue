<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { checkAnswer, getRandomQuestion, readableApiError } from '../api/questions'
import MarkdownContent from '../components/MarkdownContent.vue'
import QuizOption from '../components/QuizOption.vue'
import {
  configureSession,
  quizSession,
  recordAnswer,
  resetSession,
  sessionStats,
} from '../stores/quizSession'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const question = ref(null)
const selectedAnswer = ref('')
const result = ref(null)
const loadError = ref('')
const stageDraft = ref(quizSession.stage)
const targetDraft = ref(quizSession.target)

const stages = [
  { value: 0, label: '全部阶段 · 综合练习' },
  { value: 1, label: '阶段 1 · 输出与基础语法' },
  { value: 2, label: '阶段 2 · 变量与数据类型' },
  { value: 3, label: '阶段 3 · 运算符与表达式' },
  { value: 4, label: '阶段 4 · 字符串' },
  { value: 5, label: '阶段 5 · 列表与元组' },
  { value: 6, label: '阶段 6 · 字典与集合' },
  { value: 7, label: '阶段 7 · 条件判断' },
  { value: 8, label: '阶段 8 · 循环' },
  { value: 9, label: '阶段 9 · 函数' },
  { value: 10, label: '阶段 10 · 异常、模块与面向对象' },
]

const options = computed(() => {
  if (!question.value) return []
  return ['A', 'B', 'C', 'D'].map((label) => ({
    label,
    content: question.value[`option_${label.toLowerCase()}`],
  }))
})

const progress = computed(() =>
  Math.min(100, Math.round((sessionStats.total.value / quizSession.target) * 100)),
)
const sessionFinished = computed(() => sessionStats.total.value >= quizSession.target)

async function loadQuestion() {
  loading.value = true
  loadError.value = ''
  selectedAnswer.value = ''
  result.value = null
  try {
    const excludeIds = quizSession.history.map((item) => item.questionId)
    const response = await getRandomQuestion({
      excludeIds,
      stage: quizSession.stage,
    })
    question.value = response.data
  } catch (error) {
    question.value = null
    loadError.value = readableApiError(error, '题目加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
}

function optionStatus(label) {
  if (!result.value) {
    return { selected: selectedAnswer.value === label }
  }
  return {
    selected: selectedAnswer.value === label,
    correct: result.value.correct_answer === label,
    wrong: selectedAnswer.value === label && !result.value.is_correct,
  }
}

async function submitAnswer() {
  if (!selectedAnswer.value) {
    ElMessage.warning('请先选择一个答案')
    return
  }
  if (!question.value || result.value) return

  submitting.value = true
  try {
    const response = await checkAnswer(question.value.id, selectedAnswer.value)
    result.value = response.data
    recordAnswer({
      questionId: question.value.id,
      title: question.value.title.split('\n')[0],
      selectedAnswer: selectedAnswer.value,
      correctAnswer: response.data.correct_answer,
      isCorrect: response.data.is_correct,
    })
  } catch (error) {
    ElMessage.error(readableApiError(error, '提交失败，请稍后重试'))
  } finally {
    submitting.value = false
  }
}

async function applySessionSettings() {
  if (stageDraft.value === quizSession.stage && targetDraft.value === quizSession.target) return

  if (sessionStats.total.value > 0) {
    try {
      await ElMessageBox.confirm('更换阶段或题数会清空本轮统计，是否继续？', '重新开始', {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      stageDraft.value = quizSession.stage
      targetDraft.value = quizSession.target
      return
    }
  }

  configureSession({ stage: stageDraft.value, target: targetDraft.value })
  resetSession()
  await loadQuestion()
}

async function restart() {
  resetSession()
  await loadQuestion()
}

function nextStep() {
  if (sessionFinished.value) {
    router.push('/stats')
  } else {
    loadQuestion()
  }
}

onMounted(() => {
  if (sessionFinished.value) {
    router.push('/stats')
  } else {
    loadQuestion()
  }
})
</script>

<template>
  <section class="quiz-page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">10,000 道新手练习题</span>
        <h1>一步一步学 Python</h1>
        <p>选择学习阶段，读题后提交答案，立即获得判题和解析。</p>
      </div>
      <div class="session-summary" aria-label="本轮答题统计">
        <span>已答 <strong>{{ sessionStats.total.value }}</strong></span>
        <span>答对 <strong>{{ sessionStats.correct.value }}</strong></span>
        <span>正确率 <strong>{{ sessionStats.accuracy.value }}%</strong></span>
      </div>
    </div>

    <el-card class="settings-card" shadow="never">
      <div class="settings-row">
        <label>
          <span>学习阶段</span>
          <el-select v-model="stageDraft" class="stage-select" @change="applySessionSettings">
            <el-option
              v-for="stage in stages"
              :key="stage.value"
              :label="stage.label"
              :value="stage.value"
            />
          </el-select>
        </label>
        <label>
          <span>本轮题数</span>
          <el-select v-model="targetDraft" class="target-select" @change="applySessionSettings">
            <el-option label="10 题" :value="10" />
            <el-option label="20 题" :value="20" />
            <el-option label="50 题" :value="50" />
          </el-select>
        </label>
        <el-button text type="primary" @click="restart">重新开始</el-button>
      </div>
      <el-progress :percentage="progress" :show-text="false" :stroke-width="8" />
    </el-card>

    <el-skeleton v-if="loading" class="question-skeleton" :rows="8" animated />

    <el-empty v-else-if="loadError" :description="loadError">
      <el-button type="primary" @click="loadQuestion">重新加载</el-button>
    </el-empty>

    <article v-else-if="question" class="question-card">
      <div class="question-meta">
        <span>第 {{ sessionStats.total.value + (result ? 0 : 1) }} / {{ quizSession.target }} 题</span>
        <span>单选题</span>
      </div>

      <MarkdownContent class="question-title" :content="question.title" />

      <div class="options-grid" role="radiogroup" aria-label="答案选项">
        <QuizOption
          v-for="option in options"
          :key="option.label"
          :label="option.label"
          :content="option.content"
          :selected="optionStatus(option.label).selected"
          :correct="optionStatus(option.label).correct"
          :wrong="optionStatus(option.label).wrong"
          :locked="Boolean(result)"
          @choose="selectedAnswer = option.label"
        />
      </div>

      <transition name="feedback">
        <div v-if="result" class="answer-feedback" :class="result.is_correct ? 'success' : 'error'">
          <div class="feedback-heading">
            <span class="feedback-icon">{{ result.is_correct ? '✓' : '×' }}</span>
            <div>
              <strong>{{ result.is_correct ? '回答正确！' : '回答错误' }}</strong>
              <p v-if="!result.is_correct">正确答案是 {{ result.correct_answer }}</p>
            </div>
          </div>
          <div class="analysis-block">
            <span>答案解析</span>
            <MarkdownContent :content="result.analysis" />
          </div>
        </div>
      </transition>

      <div class="question-actions">
        <el-button v-if="!result" type="primary" size="large" :loading="submitting" @click="submitAnswer">
          提交答案
        </el-button>
        <el-button v-else type="primary" size="large" @click="nextStep">
          {{ sessionFinished ? '查看本轮成绩' : '下一题' }}
        </el-button>
        <el-button v-if="sessionStats.total.value" size="large" @click="router.push('/stats')">
          查看统计
        </el-button>
      </div>
    </article>
  </section>
</template>

