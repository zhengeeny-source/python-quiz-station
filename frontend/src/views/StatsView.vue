<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { quizSession, resetSession, sessionStats } from '../stores/quizSession'

const router = useRouter()
const wrongCount = computed(() => sessionStats.total.value - sessionStats.correct.value)
const progressStatus = computed(() => {
  if (!sessionStats.total.value) return undefined
  if (sessionStats.accuracy.value >= 80) return 'success'
  if (sessionStats.accuracy.value < 60) return 'exception'
  return undefined
})

function startAgain() {
  resetSession()
  router.push('/')
}
</script>

<template>
  <section class="stats-page">
    <div class="page-heading compact">
      <div>
        <span class="eyebrow">SESSION REPORT</span>
        <h1>本次答题统计</h1>
        <p>数据只保存在当前浏览器会话中，不需要登录。</p>
      </div>
    </div>

    <el-empty v-if="!sessionStats.total.value" description="本轮还没有答题记录">
      <el-button type="primary" @click="router.push('/')">开始刷题</el-button>
    </el-empty>

    <template v-else>
      <div class="score-card">
        <el-progress
          type="dashboard"
          :percentage="sessionStats.accuracy.value"
          :status="progressStatus"
          :width="190"
          :stroke-width="14"
        />
        <div class="score-copy">
          <span>本轮成绩</span>
          <h2>{{ sessionStats.correct.value }} / {{ sessionStats.total.value }}</h2>
          <p v-if="sessionStats.accuracy.value >= 80">掌握得不错，继续保持！</p>
          <p v-else-if="sessionStats.accuracy.value >= 60">基础正在变稳，再练一轮会更好。</p>
          <p v-else>别着急，结合解析复习后再挑战一次。</p>
        </div>
      </div>

      <div class="stat-grid">
        <div><span>完成题数</span><strong>{{ sessionStats.total.value }}</strong></div>
        <div><span>答对</span><strong class="success-text">{{ sessionStats.correct.value }}</strong></div>
        <div><span>答错</span><strong class="error-text">{{ wrongCount }}</strong></div>
        <div><span>正确率</span><strong>{{ sessionStats.accuracy.value }}%</strong></div>
      </div>

      <el-card class="answer-history" shadow="never">
        <template #header>
          <div class="history-title">
            <strong>答题明细</strong>
            <span>目标 {{ quizSession.target }} 题</span>
          </div>
        </template>
        <div v-for="(item, index) in quizSession.history" :key="item.questionId" class="history-row">
          <span class="history-index">{{ index + 1 }}</span>
          <span class="history-question">{{ item.title }}</span>
          <span :class="item.isCorrect ? 'success-text' : 'error-text'">
            {{ item.isCorrect ? '正确' : `错误（答案 ${item.correctAnswer}）` }}
          </span>
        </div>
      </el-card>

      <div class="stats-actions">
        <el-button type="primary" size="large" @click="startAgain">再练一轮</el-button>
        <el-button v-if="sessionStats.total.value < quizSession.target" size="large" @click="router.push('/')">
          继续本轮
        </el-button>
      </div>
    </template>
  </section>
</template>
