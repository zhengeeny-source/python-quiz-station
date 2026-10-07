<script setup>
import { computed } from 'vue'

import MarkdownContent from './MarkdownContent.vue'

const props = defineProps({
  label: { type: String, required: true },
  content: { type: String, required: true },
  selected: { type: Boolean, default: false },
  correct: { type: Boolean, default: false },
  wrong: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
})

defineEmits(['choose'])

const classes = computed(() => ({
  selected: props.selected && !props.locked,
  correct: props.correct,
  wrong: props.wrong,
  muted: props.locked && !props.correct && !props.wrong,
}))
</script>

<template>
  <button
    type="button"
    class="option-card"
    :class="classes"
    :disabled="locked"
    :aria-pressed="selected"
    @click="$emit('choose')"
  >
    <span class="option-label">{{ label }}</span>
    <MarkdownContent :content="content" inline />
    <span v-if="correct" class="option-state" aria-label="正确选项">✓</span>
    <span v-else-if="wrong" class="option-state" aria-label="错误选项">×</span>
  </button>
</template>

