<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
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
        </nav>
      </div>
    </header>

    <main class="page-container">
      <router-view />
    </main>

    <footer class="site-footer">Python 刷题小站 · 适合零基础学习者的 10 阶段练习</footer>
  </div>
</template>

