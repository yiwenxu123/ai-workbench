<template>
  <div class="shot-language-quiz">
    <div v-if="!quizStarted && !quizFinished" class="quiz-intro">
      <div class="intro-header">
        <component :is="Brain" :size="32" class="intro-icon" />
        <h3 class="intro-title">运镜知识测验</h3>
      </div>
      <p class="intro-desc">
        通过小测验检验你对镜头语言的掌握程度，共 {{ totalQuestions }} 道题，
        涵盖基础、进阶、高级三个难度。
      </p>
      <div class="difficulty-select">
        <span class="select-label">选择难度：</span>
        <n-radio-group v-model:value="selectedDifficulty" type="button" size="small">
          <n-radio-button value="all">全部</n-radio-button>
          <n-radio-button value="basic">入门</n-radio-button>
          <n-radio-button value="intermediate">进阶</n-radio-button>
          <n-radio-button value="advanced">高级</n-radio-button>
        </n-radio-group>
      </div>
      <n-button type="primary" size="large" block @click="startQuiz">
        开始测验
      </n-button>
    </div>

    <div v-else-if="quizStarted && !quizFinished" class="quiz-in-progress">
      <div class="quiz-progress-bar">
        <div class="progress-info">
          <span>第 {{ currentIndex + 1 }} / {{ questions.length }} 题</span>
          <span class="score-label">得分：{{ score }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="Math.round(((currentIndex + 1) / questions.length) * 100)"
          :show-indicator="false"
          height="6"
        />
      </div>

      <div class="question-card">
        <div class="question-header">
          <n-tag :type="getDifficultyTagType(currentQuestion.category)" size="small">
            {{ getDifficultyLabel(currentQuestion.category) }}
          </n-tag>
          <span v-if="currentQuestion.relatedMovement" class="related-link">
            <n-button text size="tiny" @click="goToMovement(currentQuestion.relatedMovement!)">
              查看相关运镜 →
            </n-button>
          </span>
        </div>
        <h4 class="question-text">{{ currentQuestion.question }}</h4>
        <div class="options-list">
          <div
            v-for="(option, idx) in currentQuestion.options"
            :key="option.value"
            class="option-item"
            :class="{
              selected: selectedAnswer === option.value,
              correct: showResult && option.value === currentQuestion.correctAnswer,
              wrong: showResult && selectedAnswer === option.value && option.value !== currentQuestion.correctAnswer,
              disabled: showResult,
            }"
            @click="selectAnswer(option.value)"
          >
            <span class="option-label">{{ String.fromCharCode(65 + idx) }}</span>
            <span class="option-text">{{ option.label }}</span>
          </div>
        </div>

        <div v-if="showResult" class="result-section">
          <n-alert :type="isCorrect ? 'success' : 'error'" :show-icon="true">
            <template #header>
              {{ isCorrect ? '回答正确！' : '回答错误' }}
            </template>
            <p class="explanation-text">{{ currentQuestion.explanation }}</p>
          </n-alert>
        </div>

        <div class="question-actions">
          <n-button v-if="!showResult" :disabled="!selectedAnswer" type="primary" @click="submitAnswer">
            确认答案
          </n-button>
          <n-button v-else-if="currentIndex < questions.length - 1" type="primary" @click="nextQuestion">
            下一题
          </n-button>
          <n-button v-else type="primary" @click="finishQuiz">
            查看结果
          </n-button>
        </div>
      </div>
    </div>

    <div v-else class="quiz-result">
      <div class="result-header">
        <component :is="Trophy" :size="48" class="trophy-icon" :class="resultGrade" />
        <h3 class="result-title">{{ resultTitle }}</h3>
        <div class="result-score">
          <span class="score-number">{{ score }}</span>
          <span class="score-total">/ {{ questions.length }}</span>
        </div>
        <p class="result-desc">{{ resultDescription }}</p>
      </div>

      <div class="result-stats">
        <div class="stat-item">
          <span class="stat-label">正确率</span>
          <span class="stat-value">{{ Math.round((score / questions.length) * 100) }}%</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">答对</span>
          <span class="stat-value success">{{ score }} 题</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">答错</span>
          <span class="stat-value error">{{ questions.length - score }} 题</span>
        </div>
      </div>

      <div v-if="wrongAnswers.length > 0" class="wrong-review">
        <h4 class="review-title">错题回顾</h4>
        <div v-for="(item, idx) in wrongAnswers" :key="item.question.id" class="wrong-item">
          <div class="wrong-question">
            <span class="wrong-num">{{ idx + 1 }}.</span>
            {{ item.question.question }}
          </div>
          <div class="wrong-detail">
            <span class="detail-label">你的答案：</span>
            <span class="wrong-answer">{{ getOptionLabel(item.question, item.userAnswer) }}</span>
          </div>
          <div class="wrong-detail">
            <span class="detail-label">正确答案：</span>
            <span class="correct-answer">
              {{ getOptionLabel(item.question, item.question.correctAnswer) }}
            </span>
          </div>
          <p class="wrong-explanation">{{ item.question.explanation }}</p>
        </div>
      </div>

      <div class="result-actions">
        <n-button type="primary" block @click="restartQuiz">
          再来一次
        </n-button>
        <n-button block @click="$emit('close')">
          返回学习
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { shotLanguageQuiz } from '../../data/shotLanguage'
import type { QuizQuestion } from '../../data/shotLanguage'
import { Brain, Trophy } from 'lucide-vue-next'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'go-to-movement', movementId: string): void
}>()

const selectedDifficulty = ref<'all' | 'basic' | 'intermediate' | 'advanced'>('all')
const quizStarted = ref(false)
const quizFinished = ref(false)
const currentIndex = ref(0)
const selectedAnswer = ref<string | null>(null)
const showResult = ref(false)
const score = ref(0)
const wrongAnswers = ref<{ question: QuizQuestion; userAnswer: string }[]>([])

const filteredQuestions = computed(() => {
  if (selectedDifficulty.value === 'all') return shotLanguageQuiz
  return shotLanguageQuiz.filter((q) => q.category === selectedDifficulty.value)
})

const questions = ref<QuizQuestion[]>([])
const totalQuestions = computed(() => filteredQuestions.value.length)

const currentQuestion = computed(() => questions.value[currentIndex.value])

const isCorrect = computed(() => {
  return selectedAnswer.value === currentQuestion.value?.correctAnswer
})

function getDifficultyLabel(cat: string): string {
  const map: Record<string, string> = {
    basic: '入门',
    intermediate: '进阶',
    advanced: '高级',
  }
  return map[cat] || cat
}

function getDifficultyTagType(cat: string): 'info' | 'warning' | 'error' {
  const map: Record<string, 'info' | 'warning' | 'error'> = {
    basic: 'info',
    intermediate: 'warning',
    advanced: 'error',
  }
  return map[cat] || 'info'
}

function startQuiz() {
  questions.value = shuffleArray([...filteredQuestions.value])
  currentIndex.value = 0
  score.value = 0
  wrongAnswers.value = []
  selectedAnswer.value = null
  showResult.value = false
  quizStarted.value = true
  quizFinished.value = false
}

function selectAnswer(value: string) {
  if (showResult.value) return
  selectedAnswer.value = value
}

function submitAnswer() {
  if (!selectedAnswer.value) return
  showResult.value = true
  if (isCorrect.value) {
    score.value++
  } else {
    wrongAnswers.value.push({
      question: currentQuestion.value,
      userAnswer: selectedAnswer.value,
    })
  }
}

function nextQuestion() {
  currentIndex.value++
  selectedAnswer.value = null
  showResult.value = false
}

function finishQuiz() {
  quizFinished.value = true
}

function restartQuiz() {
  quizStarted.value = false
  quizFinished.value = false
}

function goToMovement(movementId: string) {
  emit('go-to-movement', movementId)
}

function getOptionLabel(question: QuizQuestion, value: string): string {
  const opt = question.options.find((o) => o.value === value)
  return opt ? opt.label : value
}

const resultGrade = computed(() => {
  const pct = score.value / questions.value.length
  if (pct >= 0.9) return 'excellent'
  if (pct >= 0.7) return 'good'
  if (pct >= 0.5) return 'pass'
  return 'fail'
})

const resultTitle = computed(() => {
  const pct = score.value / questions.value.length
  if (pct >= 0.9) return '运镜大师！'
  if (pct >= 0.7) return '表现不错！'
  if (pct >= 0.5) return '继续加油！'
  return '需要多练习'
})

const resultDescription = computed(() => {
  const pct = score.value / questions.value.length
  if (pct >= 0.9) return '你对镜头语言的掌握非常扎实，可以尝试更高级的运镜组合了。'
  if (pct >= 0.7) return '基础扎实，但还有一些知识点需要巩固，建议复习错题。'
  if (pct >= 0.5) return '对运镜有基本了解，建议多看看知识库中的运镜详解。'
  return '建议先系统学习知识库中的运镜知识，再来挑战。'
})

function shuffleArray<T>(arr: T[]): T[] {
  const result = [...arr]
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}
</script>

<style scoped>
.shot-language-quiz {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quiz-intro {
  padding: 24px;
  text-align: center;
}

.intro-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.intro-icon {
  color: var(--primary-color);
}

.intro-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: var(--text-color-1);
}

.intro-desc {
  font-size: 14px;
  color: var(--text-color-2);
  line-height: 1.6;
  margin: 0 0 20px 0;
}

.difficulty-select {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.select-label {
  font-size: 13px;
  color: var(--text-color-2);
}

.quiz-in-progress {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quiz-progress-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-color-2);
}

.score-label {
  font-weight: 500;
  color: var(--primary-color);
}

.question-card {
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--item-bg-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.related-link {
  font-size: 12px;
}

.question-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color-1);
  line-height: 1.6;
  margin: 0;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-item:hover:not(.disabled) {
  border-color: var(--primary-color-hover);
  background: var(--item-bg-color-hover);
}

.option-item.selected {
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.05);
}

.option-item.correct {
  border-color: var(--n-success-color, #18a058);
  background: rgba(24, 160, 88, 0.08);
}

.option-item.wrong {
  border-color: var(--n-error-color, #d03050);
  background: rgba(208, 48, 80, 0.08);
}

.option-item.disabled {
  cursor: default;
}

.option-label {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--item-bg-color-hover);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color-2);
  flex-shrink: 0;
}

.option-item.correct .option-label {
  background: var(--n-success-color, #18a058);
  color: white;
}

.option-item.wrong .option-label {
  background: var(--n-error-color, #d03050);
  color: white;
}

.option-text {
  font-size: 14px;
  color: var(--text-color-1);
  line-height: 1.5;
  padding-top: 2px;
}

.result-section {
  margin-top: 4px;
}

.explanation-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-color-2);
}

.question-actions {
  display: flex;
  justify-content: flex-end;
}

.quiz-result {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.trophy-icon {
  color: #f59e0b;
}

.trophy-icon.excellent {
  color: #f59e0b;
}

.trophy-icon.good {
  color: #3b82f6;
}

.trophy-icon.pass {
  color: #6b7280;
}

.trophy-icon.fail {
  color: #9ca3af;
}

.result-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: var(--text-color-1);
}

.result-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.score-number {
  font-size: 48px;
  font-weight: 700;
  color: var(--primary-color);
  line-height: 1;
}

.score-total {
  font-size: 18px;
  color: var(--text-color-3);
}

.result-desc {
  font-size: 14px;
  color: var(--text-color-2);
  margin: 0;
  max-width: 320px;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px;
  background: var(--item-bg-color);
  border-radius: 8px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-color-3);
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color-1);
}

.stat-value.success {
  color: var(--n-success-color, #18a058);
}

.stat-value.error {
  color: var(--n-error-color, #d03050);
}

.wrong-review {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.review-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: var(--text-color-1);
}

.wrong-item {
  padding: 14px;
  background: var(--item-bg-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wrong-question {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color-1);
  line-height: 1.5;
}

.wrong-num {
  color: var(--text-color-3);
}

.wrong-detail {
  font-size: 13px;
}

.detail-label {
  color: var(--text-color-3);
}

.wrong-answer {
  color: var(--n-error-color, #d03050);
  font-weight: 500;
}

.correct-answer {
  color: var(--n-success-color, #18a058);
  font-weight: 500;
}

.wrong-explanation {
  font-size: 12px;
  color: var(--text-color-2);
  line-height: 1.5;
  margin: 0;
  padding-top: 4px;
  border-top: 1px dashed var(--border-color);
}

.result-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
