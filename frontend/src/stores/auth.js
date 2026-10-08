import { computed, reactive } from 'vue'

import {
  AUTH_TOKEN_KEY,
  getCurrentUser,
  loginAccount,
  registerAccount,
} from '../api/questions'

export const AUTH_USER_KEY = 'python-quiz-auth-user-v1'

function cachedUser() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_USER_KEY))
  } catch {
    return null
  }
}

export const authState = reactive({
  user: localStorage.getItem(AUTH_TOKEN_KEY) ? cachedUser() : null,
  ready: false,
})

export const isLoggedIn = computed(() => Boolean(authState.user))

function saveSession(data) {
  localStorage.setItem(AUTH_TOKEN_KEY, data.access_token)
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user))
  authState.user = data.user
  window.dispatchEvent(new CustomEvent('quiz-auth-changed', { detail: data.user }))
}

export async function initializeAuth() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  if (!token) {
    authState.ready = true
    return
  }
  try {
    const response = await getCurrentUser()
    authState.user = response.data
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(response.data))
    window.dispatchEvent(new CustomEvent('quiz-auth-changed', { detail: response.data }))
  } catch {
    // 网络暂时不可用时保留缓存账号；无效 token 会由响应拦截器清理。
    if (!localStorage.getItem(AUTH_TOKEN_KEY)) authState.user = null
  } finally {
    authState.ready = true
  }
}

export async function login(username, password) {
  const response = await loginAccount(username, password)
  saveSession(response.data)
  return response.data.user
}

export async function register(username, password) {
  const response = await registerAccount(username, password)
  saveSession(response.data)
  return response.data.user
}

export function logout() {
  localStorage.removeItem(AUTH_TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
  authState.user = null
  window.dispatchEvent(new CustomEvent('quiz-auth-changed', { detail: null }))
}

window.addEventListener('quiz-auth-expired', () => {
  localStorage.removeItem(AUTH_USER_KEY)
  authState.user = null
  authState.ready = true
  window.dispatchEvent(new CustomEvent('quiz-auth-changed', { detail: null }))
})
