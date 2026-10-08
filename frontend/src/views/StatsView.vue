<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { getProgressHistory, getProgressSummary } from '../api/questions'
import { authState } from '../stores/auth'
import { quizSession, resetSession, sessionStats } from '../stores/quizSession'

const router = useRouter()
const accountProgress = ref(null)
const accountHistory = ref([])
const progressLoading = ref(false)
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

async function loadAccountProgress() {
  if (!authState.user) {
    accountProgress.value = null
    accountHistory.value = []
    return
  }
  progressLoading.value = true
  try {
    const [summary, history] = await Promise.all([
      getProgressSummary(),
      getProgressHistory(50),
    ])
    accountProgress.value = summary.data
    accountHistory.value = history.data
  } finally {
    progressLoading.value = false
  }
}

onMounted(loadAccountProgress)
watch(() => authState.user?.id, loadAccountProgress)
</script>

<template>
  <section class="stats-page">
    <div class="page-heading compact">
      <div>
        <span class="eyebrow">SESSION REPORT</span>
        <h1>本次答题统计</h1>
        <p v-if="authState.user">{{ authState.user.username }} 的累计记录已保存到云端数据库。</p>
        <p v-else>当前只显示本机记录；登录后可以跨浏览器和设备保存进度。</p>
      </div>
    </div>

    <el-card v-if="authState.user" class="account-progress" shadow="never">
      <template #header>
        <div class="history-title">
          <strong>账号累计学习记录</strong>
          <span>{{ progressLoading ? '正在加载…' : `已完成 ${accountProgress?.unique_questions || 0} 道不同题目` }}</span>
        </div>
      </template>
      <div class="stat-grid account-stat-grid">
        <div><span>累计作答</span><strong>{{ accountProgress?.total_answered || 0 }}</strong></div>
        <div><span>累计答对</span><strong class="success-text">{{ accountProgress?.correct_count || 0 }}</strong></div>
        <div><span>累计答错</span><strong class="error-text">{{ accountProgress?.wrong_count || 0 }}</strong></div>
        <div><span>累计正确率</span><strong>{{ accountProgress?.accuracy || 0 }}%</strong></div>
      </div>
      <div v-if="accountHistory.length" class="cloud-history">
        <div v-for="item in accountHistory" :key="item.id" class="history-row">
          <span class="history-index">{{ item.is_correct ? '✓' : '×' }}</span>
          <span class="history-question">{{ item.title.split('\n')[0] }}</span>
          <span :class="item.is_correct ? 'success-text' : 'error-text'">
            {{ item.is_correct ? '正确' : '错误' }}
          </span>
        </div>
      </div>
      <el-empty v-else description="登录后完成一道题，这里会出现永久记录" />
    </el-card>

    <el-alert
      v-else
      title="登录后可将答题记录保存到云端，并自动避开已经做过的题目。"
      type="info"
      :closable="false"
      show-icon
    >
      <template #default>
        <el-button type="primary" text @click="router.push('/login?redirect=/stats')">去登录或注册</el-button>
      </template>
    </el-alert>

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
