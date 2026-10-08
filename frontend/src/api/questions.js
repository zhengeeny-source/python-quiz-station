import axios from 'axios'

const configuredBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
export const AUTH_TOKEN_KEY = 'python-quiz-auth-token-v1'

const api = axios.create({
  baseURL: `${configuredBase}/api`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && localStorage.getItem(AUTH_TOKEN_KEY)) {
      localStorage.removeItem(AUTH_TOKEN_KEY)
      window.dispatchEvent(new CustomEvent('quiz-auth-expired'))
    }
    return Promise.reject(error)
  },
)

export function getRandomQuestion({ excludeIds = [], stage = null } = {}) {
  return api.get('/question/random', {
    params: {
      exclude_ids: excludeIds.length ? excludeIds.join(',') : undefined,
      stage: stage || undefined,
    },
  })
}

export function checkAnswer(questionId, selectedAnswer) {
  return api.post('/question/check', {
    question_id: questionId,
    selected_answer: selectedAnswer,
  })
}

export function addQuestion(question) {
  return api.post('/question/add', question)
}

export function listQuestions() {
  return api.get('/question/list')
}

export function registerAccount(username, password) {
  return api.post('/auth/register', { username, password })
}

export function loginAccount(username, password) {
  return api.post('/auth/login', { username, password })
}

export function getCurrentUser() {
  return api.get('/auth/me')
}

export function getProgressSummary() {
  return api.get('/progress/summary')
}

export function getProgressHistory(limit = 50) {
  return api.get('/progress/history', { params: { limit } })
}

export function readableApiError(error, fallback = '请求失败，请稍后重试') {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join('；')
  }
  return typeof detail === 'string' ? detail : fallback
}
