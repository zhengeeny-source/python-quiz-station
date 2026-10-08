<template>
  <view class="page-shell">
    <view class="hero">
      <text class="eyebrow">SESSION REPORT</text>
      <text class="page-title">学习统计</text>
      <text class="page-subtitle">
        {{ authState.user ? `${authState.user.username} 的累计记录已保存到云端。` : '访客记录只保存在本机，登录后可跨设备同步。' }}
      </text>
    </view>

    <view v-if="authState.user" class="card">
      <view class="section-heading">
        <text>账号累计学习记录</text>
        <text class="section-note">已完成 {{ accountProgress?.unique_questions || 0 }} 道不同题目</text>
      </view>
      <view class="stat-grid">
        <view><text>累计作答</text><text class="stat-value">{{ accountProgress?.total_answered || 0 }}</text></view>
        <view><text>累计答对</text><text class="stat-value success-text">{{ accountProgress?.correct_count || 0 }}</text></view>
        <view><text>累计答错</text><text class="stat-value error-text">{{ accountProgress?.wrong_count || 0 }}</text></view>
        <view><text>正确率</text><text class="stat-value">{{ accountProgress?.accuracy || 0 }}%</text></view>
      </view>
      <view v-if="progressLoading" class="loading-note">正在读取云端记录…</view>
      <view v-else-if="accountHistory.length" class="history-list">
        <view v-for="item in accountHistory" :key="item.id" class="history-row">
          <text class="history-icon" :class="item.is_correct ? 'success-text' : 'error-text'">{{ item.is_correct ? '✓' : '×' }}</text>
          <text class="history-title">{{ item.title.split('\n')[0] }}</text>
          <text :class="item.is_correct ? 'success-text' : 'error-text'">{{ item.is_correct ? '正确' : '错误' }}</text>
        </view>
      </view>
      <view v-else class="empty-state">完成一道题后，这里会显示永久记录。</view>
    </view>

    <view v-else class="card login-tip">
      <text>登录后可保存进度，并自动避开已经做过的题目。</text>
      <button class="primary-button" @click="goAccount">去登录或注册</button>
    </view>

    <view class="card session-card">
      <view class="score-ring">
        <text class="score-number">{{ stats.accuracy }}%</text>
        <text class="score-label">本轮正确率</text>
      </view>
      <view class="session-copy">
        <text class="session-score">{{ stats.correct }} / {{ stats.total }}</text>
        <text>{{ encouragement }}</text>
      </view>
    </view>

    <view class="card stat-grid local-stats">
      <view><text>完成题数</text><text class="stat-value">{{ stats.total }}</text></view>
      <view><text>答对</text><text class="stat-value success-text">{{ stats.correct }}</text></view>
      <view><text>答错</text><text class="stat-value error-text">{{ stats.wrong }}</text></view>
      <view><text>目标</text><text class="stat-value">{{ quizSession.target }}</text></view>
    </view>

    <view v-if="quizSession.history.length" class="card">
      <view class="section-heading"><text>本轮答题明细</text></view>
      <view class="history-list">
        <view v-for="(item, index) in quizSession.history" :key="item.questionId" class="history-row">
          <text class="history-index">{{ index + 1 }}</text>
          <text class="history-title">{{ item.title }}</text>
          <text :class="item.isCorrect ? 'success-text' : 'error-text'">{{ item.isCorrect ? '正确' : '错误' }}</text>
        </view>
      </view>
    </view>

    <button class="primary-button" @click="startAgain">再练一轮</button>
  </view>
</template>

<script>
import { getProgressHistory, getProgressSummary, readableApiError } from '../../api/client'
import { authState, initializeAuth } from '../../stores/auth'
import { getSessionStats, quizSession, resetSession } from '../../stores/quizSession'

export default {
  data() {
    return {
      authState,
      quizSession,
      accountProgress: null,
      accountHistory: [],
      progressLoading: false,
    }
  },
  computed: {
    stats() {
      return getSessionStats()
    },
    encouragement() {
      if (!this.stats.total) return '本轮还没有答题记录。'
      if (this.stats.accuracy >= 80) return '掌握得不错，继续保持！'
      if (this.stats.accuracy >= 60) return '基础正在变稳，再练一轮会更好。'
      return '结合解析复习后，再挑战一次。'
    },
  },
  async onShow() {
    await initializeAuth()
    this.loadAccountProgress()
  },
  methods: {
    async loadAccountProgress() {
      if (!this.authState.user) {
        this.accountProgress = null
        this.accountHistory = []
        return
      }
      this.progressLoading = true
      try {
        const [summary, history] = await Promise.all([
          getProgressSummary(),
          getProgressHistory(50),
        ])
        this.accountProgress = summary
        this.accountHistory = history
      } catch (error) {
        uni.showToast({ title: readableApiError(error, '累计记录加载失败'), icon: 'none' })
      } finally {
        this.progressLoading = false
      }
    },
    goAccount() {
      uni.switchTab({ url: '/pages/account/index' })
    },
    startAgain() {
      resetSession()
      uni.switchTab({ url: '/pages/quiz/index' })
    },
  },
}
</script>

<style scoped>
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
  font-size: 29rpx;
  font-weight: 800;
}

.section-note {
  color: #667085;
  font-size: 22rpx;
  font-weight: 400;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18rpx;
}

.stat-grid > view {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  padding: 20rpx;
  border-radius: 16rpx;
  background: #f8fafc;
  color: #667085;
}

.stat-value {
  color: #101828;
  font-size: 34rpx;
  font-weight: 800;
}

.loading-note,
.empty-state {
  color: #667085;
  text-align: center;
}

.loading-note {
  padding: 28rpx 0 10rpx;
}

.history-list {
  margin-top: 22rpx;
}

.history-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 20rpx 0;
  border-top: 2rpx solid #eaecf0;
  font-size: 25rpx;
}

.history-icon,
.history-index {
  width: 42rpx;
  flex: 0 0 42rpx;
  font-weight: 800;
  text-align: center;
}

.history-title {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: #344054;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.login-tip {
  color: #475467;
  line-height: 1.6;
}

.login-tip button {
  margin-top: 22rpx;
}

.session-card {
  display: flex;
  align-items: center;
  gap: 30rpx;
}

.score-ring {
  display: flex;
  width: 190rpx;
  height: 190rpx;
  flex: 0 0 190rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 16rpx solid #bfdbfe;
  border-radius: 50%;
}

.score-number {
  color: #1d4ed8;
  font-size: 38rpx;
  font-weight: 800;
}

.score-label {
  margin-top: 4rpx;
  color: #667085;
  font-size: 21rpx;
}

.session-copy {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  color: #667085;
  line-height: 1.55;
}

.session-score {
  color: #101828;
  font-size: 42rpx;
  font-weight: 800;
}
</style>
