import { onMounted, onUnmounted, ref } from 'vue'

export const showcaseSectionProps = {
  isActive: {
    type: Boolean,
    default: true,
  },
  animationDirection: {
    type: String,
    default: 'down',
  },
}

export function useSectionReady(delay = 24) {
  const ready = ref(false)
  let timer = null

  onMounted(() => {
    timer = window.setTimeout(() => {
      window.requestAnimationFrame(() => {
        ready.value = true
      })
    }, delay)
  })

  onUnmounted(() => {
    if (timer) {
      window.clearTimeout(timer)
    }
  })

  return ready
}

export function useTypewriter(text, step = 75, startDelay = 220) {
  const output = ref('')
  let startTimer = null
  let interval = null

  onMounted(() => {
    let currentIndex = 0
    output.value = ''
    startTimer = window.setTimeout(() => {
      interval = window.setInterval(() => {
        currentIndex += 1
        output.value = text.slice(0, currentIndex)
        if (currentIndex >= text.length) {
          window.clearInterval(interval)
        }
      }, step)
    }, startDelay)
  })

  onUnmounted(() => {
    if (startTimer) {
      window.clearTimeout(startTimer)
    }
    if (interval) {
      window.clearInterval(interval)
    }
  })

  return output
}

export function emitShowcaseGoto(index) {
  window.dispatchEvent(new CustomEvent('showcase-goto', { detail: index }))
}
