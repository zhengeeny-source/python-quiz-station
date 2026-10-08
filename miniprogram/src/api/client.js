const API_BASE = `${(import.meta.env.VITE_API_BASE_URL || 'https://python-quiz-api.onrender.com').replace(/\/$/, '')}/api`

export const AUTH_TOKEN_KEY = 'python-quiz-auth-token-v1'
export const AUTH_USER_KEY = 'python-quiz-auth-user-v1'

function buildQuery(params = {}) {
  const values = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
  return values.length ? `?${values.join('&')}` : ''
}

function request(path, { method = 'GET', data, params } = {}) {
  const token = uni.getStorageSync(AUTH_TOKEN_KEY)
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}${buildQuery(params)}`,
      method,
      data,
      timeout: 60000,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data)
          return
        }
        if (response.statusCode === 401 && token) {
          uni.removeStorageSync(AUTH_TOKEN_KEY)
          uni.removeStorageSync(AUTH_USER_KEY)
          uni.$emit('quiz-auth-expired')
        }
        reject({ statusCode: response.statusCode, data: response.data })
      },
      fail(error) {
        reject({ message: error.errMsg || '网络请求失败' })
      },
    })
  })
}

export function getRandomQuestion({ excludeIds = [], stage = null } = {}) {
  return request('/question/random', {
    params: {
      exclude_ids: excludeIds.length ? excludeIds.join(',') : undefined,
      stage: stage || undefined,
    },
  })
}

export function checkAnswer(questionId, selectedAnswer) {
  return request('/question/check', {
    method: 'POST',
    data: { question_id: questionId, selected_answer: selectedAnswer },
  })
}

export function addQuestion(question) {
  return request('/question/add', { method: 'POST', data: question })
}

export function registerAccount(username, password) {
  return request('/auth/register', { method: 'POST', data: { username, password } })
}

export function loginAccount(username, password) {
  return request('/auth/login', { method: 'POST', data: { username, password } })
}

export function getCurrentUser() {
  return request('/auth/me')
}

export function getProgressSummary() {
  return request('/progress/summary')
}

export function getProgressHistory(limit = 50) {
  return request('/progress/history', { params: { limit } })
}

export function readableApiError(error, fallback = '请求失败，请稍后重试') {
  const detail = error?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('；')
  if (typeof detail === 'string') return detail
  return error?.message || fallback
}
