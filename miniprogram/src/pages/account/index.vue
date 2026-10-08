<template>
  <view class="page-shell">
    <view class="hero">
      <text class="eyebrow">LEARNING ACCOUNT</text>
      <text class="page-title">{{ authState.user ? '我的学习账号' : mode === 'login' ? '登录继续学习' : '创建学习账号' }}</text>
      <text class="page-subtitle">答题记录会保存到云端，重新打开或换设备也能继续。</text>
    </view>

    <view v-if="authState.user" class="card account-card">
      <view class="avatar">{{ authState.user.username.slice(0, 1).toUpperCase() }}</view>
      <text class="username">{{ authState.user.username }}</text>
      <text class="account-note">当前账号已开启云端进度保存</text>
      <button class="primary-button" @click="goQuiz">继续刷题</button>
      <button class="danger-button" @click="handleLogout">退出登录</button>
    </view>

    <view v-else class="card auth-card">
      <view class="mode-switch">
        <view :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</view>
        <view :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</view>
      </view>

      <view class="form-field">
        <text class="field-label">用户名</text>
        <input v-model="form.username" class="text-input" maxlength="32" placeholder="3-32 位中文、字母、数字或下划线" />
      </view>
      <view class="form-field">
        <text class="field-label">密码</text>
        <input v-model="form.password" class="text-input" type="password" maxlength="128" placeholder="至少 8 位" />
      </view>
      <view v-if="mode === 'register'" class="form-field">
        <text class="field-label">确认密码</text>
        <input v-model="form.confirmPassword" class="text-input" type="password" maxlength="128" placeholder="再次输入密码" />
      </view>

      <button class="primary-button" :loading="submitting" :disabled="submitting" @click="submit">
        {{ mode === 'login' ? '登录' : '注册并登录' }}
      </button>
      <text class="security-note">密码使用 Argon2 单向哈希保存，服务器不会保存明文密码。</text>
    </view>
  </view>
</template>

<script>
import { readableApiError } from '../../api/client'
import { authState, initializeAuth, login, logout, register } from '../../stores/auth'

export default {
  data() {
    return {
      authState,
      mode: 'login',
      submitting: false,
      form: { username: '', password: '', confirmPassword: '' },
    }
  },
  onShow() {
    initializeAuth()
  },
  methods: {
    async submit() {
      const username = this.form.username.trim()
      if (username.length < 3) {
        uni.showToast({ title: '用户名至少 3 位', icon: 'none' })
        return
      }
      if (this.form.password.length < 8) {
        uni.showToast({ title: '密码至少 8 位', icon: 'none' })
        return
      }
      if (this.mode === 'register' && this.form.password !== this.form.confirmPassword) {
        uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
        return
      }
      this.submitting = true
      try {
        if (this.mode === 'register') await register(username, this.form.password)
        else await login(username, this.form.password)
        this.form = { username: '', password: '', confirmPassword: '' }
        uni.showToast({ title: this.mode === 'register' ? '注册成功' : '登录成功', icon: 'success' })
        setTimeout(() => this.goQuiz(), 500)
      } catch (error) {
        uni.showToast({
          title: readableApiError(error, this.mode === 'register' ? '注册失败' : '登录失败'),
          icon: 'none',
        })
      } finally {
        this.submitting = false
      }
    },
    handleLogout() {
      uni.showModal({
        title: '退出登录',
        content: '本机访客记录与账号记录会继续分开保存。',
        success: ({ confirm }) => {
          if (confirm) logout()
        },
      })
    },
    goQuiz() {
      uni.switchTab({ url: '/pages/quiz/index' })
    },
  },
}
</script>

<style scoped>
.mode-switch {
  display: flex;
  margin-bottom: 30rpx;
  padding: 8rpx;
  border-radius: 18rpx;
  background: #f2f4f7;
}

.mode-switch view {
  flex: 1;
  padding: 18rpx;
  border-radius: 13rpx;
  color: #667085;
  text-align: center;
}

.mode-switch .active {
  background: #ffffff;
  box-shadow: 0 4rpx 14rpx rgba(16, 24, 40, 0.08);
  color: #1d4ed8;
  font-weight: 800;
}

.security-note {
  display: block;
  margin-top: 22rpx;
  color: #98a2b3;
  font-size: 22rpx;
  line-height: 1.6;
  text-align: center;
}

.account-card {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar {
  display: flex;
  width: 120rpx;
  height: 120rpx;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 50rpx;
  font-weight: 800;
}

.username {
  margin-top: 20rpx;
  color: #101828;
  font-size: 36rpx;
  font-weight: 800;
}

.account-note {
  margin: 10rpx 0 30rpx;
  color: #667085;
}

.account-card button {
  width: 100%;
  margin-top: 16rpx;
}
</style>
