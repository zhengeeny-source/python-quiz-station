import { createRouter, createWebHistory } from 'vue-router'

// 页面组件按路由懒加载，减少移动端首次打开时需要下载的脚本体积。
const AddQuestionView = () => import('../views/AddQuestionView.vue')
const QuizView = () => import('../views/QuizView.vue')
const StatsView = () => import('../views/StatsView.vue')
const LoginView = () => import('../views/LoginView.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'quiz', component: QuizView },
    { path: '/stats', name: 'stats', component: StatsView },
    { path: '/add', name: 'add', component: AddQuestionView },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
