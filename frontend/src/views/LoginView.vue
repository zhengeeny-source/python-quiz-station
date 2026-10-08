<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { readableApiError } from '../api/questions'
import { login, register } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const mode = ref('login')
const submitting = ref(false)
const form = reactive({ username: '', password: '', confirmPassword: '' })

async function submit() {
  const username = form.username.trim()
  if (username.length < 3) {
    ElMessage.warning('用户名至少 3 位')
    return
  }
  if (form.password.length < 8) {
    ElMessage.warning('密码至少 8 位')
    return
  }
  if (mode.value === 'register' && form.password !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  submitting.value = true
  try {
    if (mode.value === 'register') {
      await register(username, form.password)
      ElMessage.success('注册成功，已自动登录')
    } else {
      await login(username, form.password)
      ElMessage.success('登录成功')
    }
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (error) {
    ElMessage.error(readableApiError(error, mode.value === 'register' ? '注册失败' : '登录失败'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <el-card class="auth-card" shadow="never">
      <div class="auth-heading">
        <span class="eyebrow">LEARNING ACCOUNT</span>
        <h1>{{ mode === 'login' ? '登录继续学习' : '创建学习账号' }}</h1>
        <p>答题记录会保存到账号，重新打开或换设备也能继续。</p>
      </div>

      <el-radio-group v-model="mode" class="auth-mode" size="large">
        <el-radio-button value="login">登录</el-radio-button>
        <el-radio-button value="register">注册</el-radio-button>
      </el-radio-group>

      <el-form label-position="top" size="large" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input
            v-model="form.username"
            maxlength="32"
            autocomplete="username"
            placeholder="3-32 位中文、字母、数字或下划线"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            maxlength="128"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            placeholder="至少 8 位"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-form-item v-if="mode === 'register'" label="确认密码">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            maxlength="128"
            autocomplete="new-password"
            placeholder="再次输入密码"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button class="auth-submit" type="primary" :loading="submitting" @click="submit">
          {{ mode === 'login' ? '登录' : '注册并登录' }}
        </el-button>
      </el-form>

      <p class="auth-note">密码使用 Argon2 单向哈希保存，服务器不会保存明文密码。</p>
    </el-card>
  </section>
</template>
