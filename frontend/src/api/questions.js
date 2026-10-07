import axios from 'axios'

const configuredBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

const api = axios.create({
  baseURL: `${configuredBase}/api`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

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

export function readableApiError(error, fallback = '请求失败，请稍后重试') {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join('；')
  }
  return typeof detail === 'string' ? detail : fallback
}

