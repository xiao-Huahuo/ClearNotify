<template>
  <LuminousFrame title="实时公共动态" eyebrow="Signal Feed" subtitle="从真实数据中提炼的公共展示事件流" :accent-start="accentStart" :accent-end="accentEnd" compact>
    <div class="feed-list">
      <TransitionGroup name="feed">
        <div v-for="item in displayFeed" :key="item.id" class="feed-item">
          <span class="feed-type">{{ item.type }}</span>
          <span class="feed-text">{{ item.text }}</span>
          <span class="feed-time">{{ item.time_label }}</span>
        </div>
      </TransitionGroup>
    </div>
  </LuminousFrame>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import LuminousFrame from './LuminousFrame.vue'

defineOptions({ name: 'SignalFeed' })

const props = defineProps({
  feed: {
    type: Array,
    default: () => [],
  },
  accentStart: {
    type: String,
    default: '#ff8f7a',
  },
  accentEnd: {
    type: String,
    default: '#58cbff',
  },
})

const displayFeed = ref([])
let timer = null
let cursor = 0

const syncFeed = () => {
  displayFeed.value = props.feed.slice(0, 6).map((item, index) => ({
    ...item,
    id: `${index}-${item.type}-${item.text}`,
  }))
  cursor = displayFeed.value.length
}

const tickFeed = () => {
  if (!props.feed.length) return
  const source = props.feed[cursor % props.feed.length]
  displayFeed.value.unshift({
    ...source,
    id: `${Date.now()}-${cursor}`,
  })
  if (displayFeed.value.length > 6) {
    displayFeed.value.pop()
  }
  cursor += 1
}

onMounted(() => {
  syncFeed()
  timer = window.setInterval(tickFeed, 3200)
})

watch(() => props.feed, syncFeed, { deep: true })

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.feed-list {
  display: grid;
  gap: 10px;
  max-height: 320px;
  overflow: hidden;
}

.feed-item {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) 64px;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background:
    linear-gradient(90deg, rgba(255, 143, 122, 0.08), transparent 24%, rgba(88, 203, 255, 0.08)),
    rgba(255, 255, 255, 0.03);
  clip-path: polygon(0 8px, 8px 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%);
}

.feed-type {
  display: inline-flex;
  justify-content: center;
  padding: 6px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
}

.feed-text {
  color: #eef4ff;
  font-size: 13px;
  line-height: 1.6;
}

.feed-time {
  color: rgba(255, 255, 255, 0.46);
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 12px;
  text-align: right;
}

.feed-enter-active,
.feed-leave-active {
  transition: opacity 0.45s ease, transform 0.45s ease;
}

.feed-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.feed-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
