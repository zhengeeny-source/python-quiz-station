<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'

hljs.registerLanguage('python', python)

const props = defineProps({
  content: { type: String, default: '' },
  inline: { type: Boolean, default: false },
})

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

const markdown = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: true,
  highlight(code, language) {
    if (language && hljs.getLanguage(language)) {
      return `<pre class="hljs"><code>${hljs.highlight(code, { language }).value}</code></pre>`
    }
    return `<pre class="hljs"><code>${escapeHtml(code)}</code></pre>`
  },
})

const rendered = computed(() =>
  props.inline ? markdown.renderInline(props.content) : markdown.render(props.content),
)
</script>

<template>
  <!-- markdown-it 禁用了原始 HTML，录入内容不会直接注入可执行标签。 -->
  <span v-if="inline" class="markdown-content inline" v-html="rendered" />
  <div v-else class="markdown-content" v-html="rendered" />
</template>

