<template>
  <div
    ref="containerRef"
    class="landing-container"
    tabindex="0"
    @wheel.prevent="handleWheel"
    @touchstart.passive="handleTouchStart"
    @touchend.passive="handleTouchEnd"
  >
    <ShowcaseHeader transparent-top top-text="light" :force-scrolled="currentSectionIndex > 0" />

    <div class="section-progress">
      <span class="progress-index">{{ String(currentSectionIndex + 1).padStart(2, '0') }}</span>
      <span class="progress-total">/ {{ String(sections.length).padStart(2, '0') }}</span>
    </div>

    <div class="section-indicators" aria-label="首页章节导航">
      <button
        v-for="(section, index) in sections"
        :key="section.id"
        class="indicator"
        :class="{ active: index === currentSectionIndex }"
        :aria-label="section.label"
        :title="section.label"
        @click="navigateToSection(index, index > currentSectionIndex ? 'down' : 'up')"
      >
        <span class="indicator-dot"></span>
        <span class="indicator-label">{{ section.label }}</span>
      </button>
    </div>

    <div class="stage-shell">
      <Transition :name="transitionName" mode="out-in">
        <component
          :is="currentSection.component"
          :key="currentSection.id"
          class="section-stage"
          :is-active="true"
          :animation-direction="animationDirection"
        />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import ShowcaseHeader from '@/components/showcase/ShowcaseHeader.vue'
import HeroSection from '@/components/showcase_landing/HeroSection.vue'
import UiShowcaseSection from '@/components/showcase_landing/UiShowcaseSection.vue'
import FeaturesSection from '@/components/showcase_landing/FeaturesSection.vue'
import ComparisonSection from '@/components/showcase_landing/ComparisonSection.vue'
import DesignPhilosophySection from '@/components/showcase_landing/DesignPhilosophySection.vue'
import HighlightsSection from '@/components/showcase_landing/HighlightsSection.vue'
import FlowSection from '@/components/showcase_landing/FlowSection.vue'
import CtaSection from '@/components/showcase_landing/CtaSection.vue'
import SponsorsSection from '@/components/showcase_landing/SponsorsSection.vue'
import FooterSection from '@/components/showcase_landing/FooterSection.vue'

const sections = [
  { id: 'hero', label: '序章', component: HeroSection },
  { id: 'ui-showcase', label: '概览', component: UiShowcaseSection },
  { id: 'features', label: '能力', component: FeaturesSection },
  { id: 'comparison', label: '选择', component: ComparisonSection },
  { id: 'philosophy', label: '理念', component: DesignPhilosophySection },
  { id: 'highlights', label: '亮点', component: HighlightsSection },
  { id: 'flow', label: '流程', component: FlowSection },
  { id: 'cta', label: '注册', component: CtaSection },
  { id: 'sponsors', label: '生态', component: SponsorsSection },
  { id: 'footer', label: '结尾', component: FooterSection },
]

const containerRef = ref(null)
const currentSectionIndex = ref(0)
const isAnimating = ref(false)
const animationDirection = ref('down')
const touchStartY = ref(0)
const unlockTimer = ref(null)
const previousBodyOverflow = ref('')

const currentSection = computed(() => sections[currentSectionIndex.value])
const transitionName = computed(() =>
  animationDirection.value === 'down' ? 'landing-slide-down' : 'landing-slide-up'
)

const lockAnimation = () => {
  if (unlockTimer.value) {
    window.clearTimeout(unlockTimer.value)
  }
  isAnimating.value = true
  unlockTimer.value = window.setTimeout(() => {
    isAnimating.value = false
  }, 960)
}

const navigateToSection = (targetIndex, direction) => {
  if (isAnimating.value) return
  if (targetIndex < 0 || targetIndex >= sections.length) return
  if (targetIndex === currentSectionIndex.value) return

  animationDirection.value = direction
  currentSectionIndex.value = targetIndex
  lockAnimation()
}

const handleWheel = (event) => {
  if (isAnimating.value) return
  if (Math.abs(event.deltaY) < 18) return

  if (event.deltaY > 0) {
    navigateToSection(currentSectionIndex.value + 1, 'down')
  } else {
    navigateToSection(currentSectionIndex.value - 1, 'up')
  }
}

const handleTouchStart = (event) => {
  touchStartY.value = event.changedTouches[0]?.clientY || 0
}

const handleTouchEnd = (event) => {
  if (isAnimating.value) return

  const touchEndY = event.changedTouches[0]?.clientY || 0
  const diff = touchStartY.value - touchEndY
  if (Math.abs(diff) < 56) return

  if (diff > 0) {
    navigateToSection(currentSectionIndex.value + 1, 'down')
  } else {
    navigateToSection(currentSectionIndex.value - 1, 'up')
  }
}

const handleKeydown = (event) => {
  if (event.key === 'ArrowDown' || event.key === 'PageDown') {
    event.preventDefault()
    navigateToSection(currentSectionIndex.value + 1, 'down')
  }

  if (event.key === 'ArrowUp' || event.key === 'PageUp') {
    event.preventDefault()
    navigateToSection(currentSectionIndex.value - 1, 'up')
  }

  if (event.key === 'Home') {
    event.preventDefault()
    navigateToSection(0, 'up')
  }

  if (event.key === 'End') {
    event.preventDefault()
    navigateToSection(sections.length - 1, 'down')
  }
}

const handleShowcaseGoto = (event) => {
  const targetIndex = Number(event.detail)
  if (Number.isNaN(targetIndex)) return
  navigateToSection(targetIndex, targetIndex >= currentSectionIndex.value ? 'down' : 'up')
}

onMounted(() => {
  previousBodyOverflow.value = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('showcase-goto', handleShowcaseGoto)
  containerRef.value?.focus()
})

onUnmounted(() => {
  document.body.style.overflow = previousBodyOverflow.value
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('showcase-goto', handleShowcaseGoto)
  if (unlockTimer.value) {
    window.clearTimeout(unlockTimer.value)
  }
})
</script>

<style scoped>
.landing-container {
  --showcase-ease: cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #090d15;
  outline: none;
}

.section-progress {
  position: fixed;
  top: 88px;
  left: clamp(18px, 3vw, 40px);
  z-index: 30;
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: rgba(255, 255, 255, 0.76);
  mix-blend-mode: difference;
  pointer-events: none;
}

.progress-index {
  font-family: 'Bahnschrift', 'DIN Alternate', sans-serif;
  font-size: 28px;
  letter-spacing: 0.08em;
}

.progress-total {
  font-size: 12px;
  letter-spacing: 0.24em;
}

.section-indicators {
  position: fixed;
  right: clamp(18px, 2.4vw, 34px);
  top: 50%;
  z-index: 35;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transform: translateY(-50%);
}

.indicator {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
}

.indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16);
  transition: transform 0.3s var(--showcase-ease), background 0.3s ease, box-shadow 0.3s ease;
}

.indicator-label {
  min-width: 36px;
  color: rgba(255, 255, 255, 0.56);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-align: right;
  opacity: 0;
  transform: translateX(6px);
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.indicator:hover .indicator-label,
.indicator.active .indicator-label {
  opacity: 1;
  transform: translateX(0);
}

.indicator.active .indicator-dot {
  transform: scale(1.28);
  background: linear-gradient(135deg, #ff8c73, #5fd1ff);
  box-shadow: 0 0 18px rgba(95, 209, 255, 0.55);
}

.stage-shell {
  position: relative;
  width: 100%;
  height: 100%;
}

.section-stage {
  width: 100%;
  height: 100%;
}

.landing-slide-down-enter-active,
.landing-slide-down-leave-active,
.landing-slide-up-enter-active,
.landing-slide-up-leave-active {
  position: absolute;
  inset: 0;
  transition:
    opacity 0.82s ease,
    transform 0.82s var(--showcase-ease);
}

.landing-slide-down-enter-from {
  opacity: 0;
  transform: translateY(100%) scale(1.02);
}

.landing-slide-down-leave-to {
  opacity: 0;
  transform: translateY(-18%) scale(0.98);
}

.landing-slide-up-enter-from {
  opacity: 0;
  transform: translateY(-100%) scale(1.02);
}

.landing-slide-up-leave-to {
  opacity: 0;
  transform: translateY(18%) scale(0.98);
}

@media (max-width: 768px) {
  .section-progress {
    top: 78px;
    left: 20px;
  }

  .section-indicators {
    right: 14px;
  }

  .indicator-label {
    display: none;
  }
}

@media (max-width: 640px) {
  .section-progress {
    font-size: 14px;
  }

  .progress-index {
    font-size: 22px;
  }
}
</style>
