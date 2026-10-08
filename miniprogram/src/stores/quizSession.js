import { reactive } from 'vue'

import { AUTH_TOKEN_KEY, AUTH_USER_KEY } from '../api/client'

const STORAGE_PREFIX = 'python-quiz-session-v2'
const INITIAL_STATE = {
  stage: 1,
  target: 10,
  history: [],
  startedAt: null,
}

function initialOwner() {
  try {
    const user = uni.getStorageSync(AUTH_USER_KEY)
    return user?.id && uni.getStorageSync(AUTH_TOKEN_KEY) ? `user-${user.id}` : 'guest'
  } catch {
    return 'guest'
  }
}

let activeOwner = initialOwner()

function storageKey(owner = activeOwner) {
  return `${STORAGE_PREFIX}:${owner}`
}

function loadState(owner = activeOwner) {
  try {
    const saved = uni.getStorageSync(storageKey(owner))
    if (saved && Array.isArray(saved.history)) return { ...INITIAL_STATE, ...saved }
  } catch {
    // 缓存损坏时回到默认练习，不影响云端记录。
  }
  return { ...INITIAL_STATE, history: [] }
}

export const quizSession = reactive(loadState())

function persist() {
  uni.setStorageSync(storageKey(), { ...quizSession, history: [...quizSession.history] })
}

export function getSessionStats() {
  const total = quizSession.history.length
  const correct = quizSession.history.filter((item) => item.isCorrect).length
  return {
    total,
    correct,
    wrong: total - correct,
    accuracy: total ? Math.round((correct / total) * 100) : 0,
  }
}

export function switchSessionOwner(user) {
  activeOwner = user ? `user-${user.id}` : 'guest'
  Object.assign(quizSession, loadState(activeOwner))
}

export function configureSession({ stage, target }) {
  quizSession.stage = Number(stage) || 0
  quizSession.target = Number(target) || 10
  persist()
}

export function recordAnswer(record) {
  if (quizSession.history.some((item) => item.questionId === record.questionId)) return
  if (!quizSession.startedAt) quizSession.startedAt = new Date().toISOString()
  quizSession.history.push({ ...record, answeredAt: new Date().toISOString() })
  persist()
}

export function resetSession({ keepSettings = true } = {}) {
  const stage = keepSettings ? quizSession.stage : INITIAL_STATE.stage
  const target = keepSettings ? quizSession.target : INITIAL_STATE.target
  Object.assign(quizSession, { stage, target, history: [], startedAt: null })
  persist()
}
