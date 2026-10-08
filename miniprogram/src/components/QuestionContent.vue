<template>
  <view class="content-block">
    <template v-for="(segment, index) in segments" :key="index">
      <text v-if="segment.type === 'text'" class="plain-text" selectable>{{ segment.value }}</text>
      <scroll-view v-else class="code-scroll" scroll-x>
        <text class="code-text" selectable>{{ segment.value }}</text>
      </scroll-view>
    </template>
  </view>
</template>

<script>
export default {
  props: {
    content: {
      type: String,
      default: '',
    },
  },
  computed: {
    segments() {
      const source = this.content || ''
      const pattern = /```(?:python)?\s*\n([\s\S]*?)```/gi
      const result = []
      let cursor = 0
      let match
      while ((match = pattern.exec(source)) !== null) {
        const before = source.slice(cursor, match.index).trim()
        if (before) result.push({ type: 'text', value: before.replace(/`([^`]+)`/g, '$1') })
        result.push({ type: 'code', value: match[1].trimEnd() })
        cursor = pattern.lastIndex
      }
      const after = source.slice(cursor).trim()
      if (after) result.push({ type: 'text', value: after.replace(/`([^`]+)`/g, '$1') })
      return result.length ? result : [{ type: 'text', value: source }]
    },
  },
}
</script>

<style scoped>
.content-block {
  width: 100%;
}

.plain-text {
  display: block;
  color: #1d2939;
  font-size: 30rpx;
  line-height: 1.7;
  white-space: pre-wrap;
}

.code-scroll {
  width: 100%;
  margin: 20rpx 0;
  padding: 22rpx;
  border-radius: 16rpx;
  background: #111827;
  color: #d1fae5;
}

.code-text {
  display: inline-block;
  min-width: 100%;
  font-family: Menlo, Monaco, Consolas, monospace;
  font-size: 25rpx;
  line-height: 1.7;
  white-space: pre;
}
</style>
