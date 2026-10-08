<template>
  <view class="page-shell">
    <view class="hero">
      <text class="eyebrow">10,000 道新手练习题</text>
      <text class="page-title">一步一步学 Python</text>
      <text class="page-subtitle">
        {{ authState.user ? `已登录为 ${authState.user.username}，记录会自动保存。` : '当前为访客模式，登录后可跨设备保存进度。' }}
      </text>
    </view>

    <view class="summary-card card">
      <view><text>已答</text><text class="summary-value">{{ stats.total }}</text></view>
      <view><text>答对</text><text class="summary-value success-text">{{ stats.correct }}</text></view>
      <view><text>正确率</text><text class="summary-value">{{ stats.accuracy }}%</text></view>
    </view>

    <view class="settings-card card">
      <view class="setting-grid">
        <view class="setting-item">
          <text class="field-label">学习阶段</text>
          <picker :range="stageLabels" :value="stageIndex" @change="changeStage">
            <view class="picker-field ellipsis">{{ currentStageLabel }}</view>
          </picker>
        </view>
        <view class="setting-item target-item">
          <text class="field-label">本轮题数</text>
          <picker :range="targetLabels" :value="targetIndex" @change="changeTarget">
            <view class="picker-field">{{ quizSession.target }} 题</view>
          </picker>
        </view>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: `${progress}%` }" />
      </view>
      <button class="restart-button" @click="restart">重新开始本轮</button>
    </view>

    <view v-if="loading" class="card loading-card">
      <view v-for="item in 6" :key="item" class="skeleton-line" :class="`line-${item}`" />
    </view>

    <view v-else-if="loadError" class="card empty-state">
      <text>{{ loadError }}</text>
      <button class="primary-button retry-button" @click="loadQuestion">重新加载</button>
    </view>

    <view v-else-if="question" class="question-card card">
      <view class="question-meta">
        <text>第 {{ stats.total + (result ? 0 : 1) }} / {{ quizSession.target }} 题</text>
        <text class="type-badge">{{ questionTypeLabel }}</text>
      </view>

      <QuestionContent :content="question.title" />

      <view v-if="question.question_type !== 'fill_blank'" class="options-list">
        <view
          v-for="option in options"
          :key="option.label"
          class="option-card"
          :class="optionClasses(option.label)"
          @click="chooseOption(option.label)"
        >
          <text class="option-letter">{{ option.label }}</text>
          <text class="option-content" selectable>{{ option.content }}</text>
          <text v-if="result && result.correct_answer === option.label" class="option-mark">✓</text>
          <text v-else-if="result && selectedAnswer === option.label && !result.is_correct" class="option-mark">×</text>
        </view>
      </view>

      <view v-else class="fill-block">
        <text class="field-label">填写运行结果</text>
        <textarea
          v-model="selectedAnswer"
          class="text-area"
          :disabled="Boolean(result)"
          placeholder="请输入答案；多行输出可直接换行"
        />
      </view>

      <view v-if="result" class="feedback" :class="result.is_correct ? 'feedback-success' : 'feedback-error'">
        <view class="feedback-title">
          <text class="feedback-icon">{{ result.is_correct ? '✓' : '×' }}</text>
          <text>{{ result.is_correct ? '回答正确！' : `回答错误，正确答案：${result.correct_answer}` }}</text>
        </view>
        <view class="analysis">
          <text class="analysis-label">答案解析</text>
          <QuestionContent :content="result.analysis" />
        </view>
      </view>

      <button
        v-if="!result"
        class="primary-button action-button"
        :loading="submitting"
        :disabled="submitting"
        @click="submitAnswer"
      >提交答案</button>
      <button v-else class="primary-button action-button" @click="nextStep">
        {{ sessionFinished ? '查看本轮成绩' : '下一题' }}
      </button>
    </view>
  </view>
</template>

<script>
import QuestionContent from '../../components/QuestionContent.vue'
import { checkAnswer, getRandomQuestion, readableApiError } from '../../api/client'
import { STAGES, TARGETS } from '../../constants/stages'
import { authState, initializeAuth } from '../../stores/auth'
import {
  configureSession,
  getSessionStats,
  quizSession,
  recordAnswer,
  resetSession,
} from '../../stores/quizSession'

export default {
  components: { QuestionContent },
  data() {
    return {
      authState,
      quizSession,
      stages: STAGES,
      targets: TARGETS,
      loading: false,
      submitting: false,
      question: null,
      selectedAnswer: '',
      result: null,
      loadError: '',
      seenUserId: null,
    }
  },
  computed: {
    stats() {
      return getSessionStats()
    },
    progress() {
      return Math.min(100, Math.round((this.stats.total / this.quizSession.target) * 100))
    },
    sessionFinished() {
      return this.stats.total >= this.quizSession.target
    },
    options() {
      if (!this.question || this.question.question_type === 'fill_blank') return []
      const letters = this.question.question_type === 'true_false' ? ['A', 'B'] : ['A', 'B', 'C', 'D']
      return letters.map((label) => ({
        label,
        content: this.question[`option_${label.toLowerCase()}`],
      }))
    },
    questionTypeLabel() {
      return {
        single_choice: '单选题',
        true_false: '判断题',
        fill_blank: '填空题',
      }[this.question?.question_type] || '练习题'
    },
    stageLabels() {
      return this.stages.map((item) => item.label)
    },
    targetLabels() {
      return this.targets.map((value) => `${value} 题`)
    },
    stageIndex() {
      return Math.max(0, this.stages.findIndex((item) => item.value === this.quizSession.stage))
    },
    targetIndex() {
      return Math.max(0, this.targets.indexOf(this.quizSession.target))
    },
    currentStageLabel() {
      return this.stages[this.stageIndex]?.label || this.stages[0].label
    },
  },
  async onLoad() {
    await initializeAuth()
    this.seenUserId = this.authState.user?.id || 0
    if (this.sessionFinished) {
      uni.switchTab({ url: '/pages/stats/index' })
      return
    }
    this.loadQuestion()
  },
  onShow() {
    const currentUserId = this.authState.user?.id || 0
    if (this.seenUserId !== null && currentUserId !== this.seenUserId) {
      this.seenUserId = currentUserId
      this.loadQuestion()
    }
  },
  methods: {
    async loadQuestion() {
      this.loading = true
      this.loadError = ''
      this.selectedAnswer = ''
      this.result = null
      try {
        this.question = await getRandomQuestion({
          excludeIds: this.quizSession.history.map((item) => item.questionId),
          stage: this.quizSession.stage,
        })
      } catch (error) {
        this.question = null
        this.loadError = readableApiError(error, '题目加载失败，请稍后重试')
      } finally {
        this.loading = false
      }
    },
    chooseOption(label) {
      if (!this.result) this.selectedAnswer = label
    },
    optionClasses(label) {
      return {
        selected: !this.result && this.selectedAnswer === label,
        correct: this.result && this.result.correct_answer === label,
        wrong: this.result && this.selectedAnswer === label && !this.result.is_correct,
      }
    },
    async submitAnswer() {
      if (!this.selectedAnswer.trim()) {
        uni.showToast({ title: '请先填写或选择答案', icon: 'none' })
        return
      }
      if (!this.question || this.result || this.submitting) return
      this.submitting = true
      try {
        this.result = await checkAnswer(this.question.id, this.selectedAnswer)
        recordAnswer({
          questionId: this.question.id,
          title: this.question.title.split('\n')[0],
          selectedAnswer: this.selectedAnswer,
          correctAnswer: this.result.correct_answer,
          isCorrect: this.result.is_correct,
        })
      } catch (error) {
        uni.showToast({ title: readableApiError(error, '提交失败，请稍后重试'), icon: 'none' })
      } finally {
        this.submitting = false
      }
    },
    nextStep() {
      if (this.sessionFinished) uni.switchTab({ url: '/pages/stats/index' })
      else this.loadQuestion()
    },
    applySettings(stage, target) {
      configureSession({ stage, target })
      resetSession()
      this.loadQuestion()
    },
    confirmSettings(stage, target) {
      if (!this.stats.total) {
        this.applySettings(stage, target)
        return
      }
      uni.showModal({
        title: '重新开始',
        content: '更换阶段或题数会清空本轮统计，是否继续？',
        success: ({ confirm }) => {
          if (confirm) this.applySettings(stage, target)
        },
      })
    },
    changeStage(event) {
      const stage = this.stages[Number(event.detail.value)]?.value ?? 0
      if (stage !== this.quizSession.stage) this.confirmSettings(stage, this.quizSession.target)
    },
    changeTarget(event) {
      const target = this.targets[Number(event.detail.value)] || 10
      if (target !== this.quizSession.target) this.confirmSettings(this.quizSession.stage, target)
    },
    restart() {
      resetSession()
      this.loadQuestion()
    },
  },
}
</script>

<style scoped>
.summary-card {
  display: flex;
  justify-content: space-around;
  text-align: center;
}

.summary-card view {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8rpx;
  color: #667085;
}

.summary-card view + view {
  border-left: 2rpx solid #eaecf0;
}

.summary-value {
  color: #101828;
  font-size: 36rpx;
  font-weight: 800;
}

.setting-grid {
  display: flex;
  gap: 18rpx;
}

.setting-item {
  min-width: 0;
  flex: 1;
}

.target-item {
  flex: 0 0 190rpx;
}

.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-track {
  height: 14rpx;
  margin-top: 24rpx;
  overflow: hidden;
  border-radius: 999rpx;
  background: #e4e7ec;
}

.progress-fill {
  height: 100%;
  border-radius: 999rpx;
  background: #2563eb;
  transition: width 0.25s ease;
}

.restart-button {
  margin: 18rpx 0 0;
  padding: 0;
  background: transparent;
  color: #2563eb;
  font-size: 25rpx;
  line-height: 54rpx;
}

.loading-card {
  min-height: 520rpx;
}

.skeleton-line {
  height: 30rpx;
  margin-bottom: 28rpx;
  border-radius: 10rpx;
  background: #eef1f5;
}

.line-2,
.line-5 {
  width: 72%;
}

.question-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22rpx;
  color: #667085;
  font-size: 24rpx;
}

.type-badge {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 26rpx;
}

.option-card {
  display: flex;
  min-height: 92rpx;
  align-items: center;
  padding: 18rpx 20rpx;
  border: 3rpx solid #e4e7ec;
  border-radius: 18rpx;
  background: #ffffff;
}

.option-card.selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.option-card.correct {
  border-color: #16a34a;
  background: #f0fdf4;
}

.option-card.wrong {
  border-color: #dc2626;
  background: #fef2f2;
}

.option-letter {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  flex: 0 0 56rpx;
  align-items: center;
  justify-content: center;
  margin-right: 18rpx;
  border-radius: 50%;
  background: #eef2ff;
  color: #3730a3;
  font-weight: 800;
}

.option-content {
  min-width: 0;
  flex: 1;
  font-size: 28rpx;
  line-height: 1.55;
}

.option-mark {
  margin-left: 12rpx;
  font-size: 36rpx;
  font-weight: 800;
}

.fill-block {
  margin-top: 28rpx;
}

.feedback {
  margin-top: 26rpx;
  padding: 24rpx;
  border-radius: 18rpx;
}

.feedback-success {
  border: 2rpx solid #86efac;
  background: #f0fdf4;
}

.feedback-error {
  border: 2rpx solid #fca5a5;
  background: #fef2f2;
}

.feedback-title {
  display: flex;
  align-items: center;
  font-size: 29rpx;
  font-weight: 800;
}

.feedback-icon {
  margin-right: 14rpx;
  font-size: 38rpx;
}

.analysis {
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 2rpx solid rgba(102, 112, 133, 0.18);
}

.analysis-label {
  display: block;
  margin-bottom: 12rpx;
  color: #475467;
  font-size: 24rpx;
  font-weight: 700;
}

.action-button,
.retry-button {
  margin-top: 28rpx;
}
</style>
