<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { authState, logout } from './stores/auth'

const route = useRoute()
const router = useRouter()

function signOut() {
  logout()
  ElMessage.success('已退出登录')
  router.push('/')
}
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <div class="header-inner">
        <router-link class="brand" to="/">
          <span class="brand-mark">Py</span>
          <span>
            <strong>Python 刷题小站</strong>
            <small>每天进步一点点</small>
          </span>
        </router-link>

        <nav class="main-nav" aria-label="主导航">
          <router-link :class="{ active: route.name === 'quiz' }" to="/">刷题</router-link>
          <router-link :class="{ active: route.name === 'stats' }" to="/stats">统计</router-link>
          <router-link :class="{ active: route.name === 'add' }" to="/add">新增题目</router-link>
          <template v-if="authState.user">
            <span class="account-name">{{ authState.user.username }}</span>
            <button class="nav-account-button" type="button" @click="signOut">退出</button>
          </template>
          <router-link v-else :class="{ active: route.name === 'login' }" to="/login">登录</router-link>
        </nav>
      </div>
    </header>

    <main class="page-container">
      <router-view />
    </main>

    <footer class="site-footer">Python 刷题小站 · 适合零基础学习者的 10 阶段练习</footer>
  </div>
</template>
