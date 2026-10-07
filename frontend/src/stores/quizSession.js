import { computed, reactive } from 'vue'

const STORAGE_KEY = 'python-quiz-session-v1'

const initialState = {
  stage: 1,
  target: 10,
  history: [],
  startedAt: null,
}

function loadState() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY))
    if (saved && Array.isArray(saved.history)) {
      return { ...initialState, ...saved }
    }
  } catch {
    // 浏览器缓存损坏时直接开始新的练习，不影响主流程。
  }
  return { ...initialState, history: [] }
}

export const quizSession = reactive(loadState())

export const sessionStats = {
  total: computed(() => quizSession.history.length),
  correct: computed(() => quizSession.history.filter((item) => item.isCorrect).length),
  accuracy: computed(() => {
    if (!quizSession.history.length) return 0
    return Math.round(
      (quizSession.history.filter((item) => item.isCorrect).length / quizSession.history.length) * 100,
    )
  }),
}

function persist() {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(quizSession))
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
  const stage = keepSettings ? quizSession.stage : initialState.stage
  const target = keepSettings ? quizSession.target : initialState.target
  quizSession.stage = stage
  quizSession.target = target
  quizSession.history = []
  quizSession.startedAt = null
  persist()
}

