import { reactive } from 'vue'

import {
  AUTH_TOKEN_KEY,
  AUTH_USER_KEY,
  getCurrentUser,
  loginAccount,
  registerAccount,
} from '../api/client'
import { switchSessionOwner } from './quizSession'

export const authState = reactive({
  user: uni.getStorageSync(AUTH_TOKEN_KEY) ? uni.getStorageSync(AUTH_USER_KEY) || null : null,
  ready: false,
})

function saveSession(data) {
  uni.setStorageSync(AUTH_TOKEN_KEY, data.access_token)
  uni.setStorageSync(AUTH_USER_KEY, data.user)
  authState.user = data.user
  authState.ready = true
  switchSessionOwner(data.user)
}

export async function initializeAuth({ force = false } = {}) {
  if (authState.ready && !force) return authState.user
  const token = uni.getStorageSync(AUTH_TOKEN_KEY)
  if (!token) {
    authState.user = null
    authState.ready = true
    switchSessionOwner(null)
    return null
  }
  try {
    const user = await getCurrentUser()
    uni.setStorageSync(AUTH_USER_KEY, user)
    authState.user = user
    switchSessionOwner(user)
  } catch {
    if (!uni.getStorageSync(AUTH_TOKEN_KEY)) {
      authState.user = null
      switchSessionOwner(null)
    }
  } finally {
    authState.ready = true
  }
  return authState.user
}

export async function login(username, password) {
  const data = await loginAccount(username, password)
  saveSession(data)
  return data.user
}

export async function register(username, password) {
  const data = await registerAccount(username, password)
  saveSession(data)
  return data.user
}

export function logout() {
  uni.removeStorageSync(AUTH_TOKEN_KEY)
  uni.removeStorageSync(AUTH_USER_KEY)
  authState.user = null
  authState.ready = true
  switchSessionOwner(null)
}

uni.$on('quiz-auth-expired', () => {
  authState.user = null
  authState.ready = true
  switchSessionOwner(null)
})
