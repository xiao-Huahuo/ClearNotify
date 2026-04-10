<template>
  <section class="intro-hero" :class="{ leaving }">
    <div class="hero-noise"></div>
    <div class="hero-glow hero-glow-one"></div>
    <div class="hero-glow hero-glow-two"></div>

    <div class="hero-inner">
      <div class="hero-orb-wrap" aria-hidden="true">
        <div class="cloudcycle-orb">
          <span class="orb-core"></span>
          <span class="orb-ring orb-ring-one"></span>
          <span class="orb-ring orb-ring-two"></span>
          <span class="orb-glow"></span>
          <span class="orb-reflection"></span>
          <span class="orb-spark"></span>
        </div>
      </div>

      <div class="hero-copy">
        <p class="hero-mark">CloudCycle</p>
        <h1>{{ typedTitle }}<span class="typing-caret"></span></h1>
        <p class="hero-subtitle">{{ typedSubtitle }}</p>

        <div class="hero-mode-preview">
          <span class="mode-chip" :class="{ active: runMode === 'agent' }">Agent 模式</span>
          <span class="mode-chip" :class="{ active: runMode === 'chat' }">Chat 模式</span>
        </div>

        <button class="enter-btn" type="button" @click="$emit('enter')">
          开始体验
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = defineProps({
  runMode: { type: String, default: 'agent' },
  leaving: { type: Boolean, default: false },
});

defineEmits(['enter']);

const TITLE = '云小圆，既会聊天，也会自主行动。';
const SUBTITLE = '以更安静、更高级的方式，把推理、工具调用和流式回答组织成同一个入口。';

const typedTitle = ref('');
const typedSubtitle = ref('');

let typingTimer = null;

const clearTypingTimer = () => {
  if (typingTimer) {
    clearTimeout(typingTimer);
    typingTimer = null;
  }
};

const typeSequence = (text, targetRef, done) => {
  let index = 0;
  const step = () => {
    targetRef.value = text.slice(0, index);
    index += 1;
    if (index <= text.length) {
      typingTimer = setTimeout(step, text === TITLE ? 58 : 28);
      return;
    }
    done?.();
  };
  step();
};

const startTyping = () => {
  clearTypingTimer();
  typedTitle.value = '';
  typedSubtitle.value = '';
  typeSequence(TITLE, typedTitle, () => {
    typingTimer = setTimeout(() => typeSequence(SUBTITLE, typedSubtitle), 220);
  });
};

watch(
  () => props.leaving,
  (leaving) => {
    if (!leaving) startTyping();
  }
);

onMounted(startTyping);
onBeforeUnmount(clearTypingTimer);
</script>

<style scoped>
.intro-hero {
  position: absolute;
  inset: 0;
  z-index: 30;
  overflow: hidden;
  background:
    radial-gradient(circle at 14% 18%, rgba(117, 172, 255, 0.5), transparent 28%),
    radial-gradient(circle at 84% 22%, rgba(116, 245, 227, 0.34), transparent 26%),
    radial-gradient(circle at 50% 82%, rgba(255, 189, 143, 0.18), transparent 20%),
    linear-gradient(180deg, rgba(248, 251, 255, 0.96), rgba(239, 245, 255, 0.84));
  transition:
    opacity 0.9s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.9s cubic-bezier(0.22, 1, 0.36, 1),
    background 0.6s ease;
}

.intro-hero,
.intro-hero * {
  transition-property: background, background-color, border-color, color, box-shadow, opacity, filter;
  transition-duration: 0.45s;
  transition-timing-function: ease;
}

.intro-hero.leaving {
  opacity: 0;
  transform: scale(1.03);
}

.hero-noise,
.hero-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-noise {
  background-image: radial-gradient(rgba(255, 255, 255, 0.56) 0.7px, transparent 0.7px);
  background-size: 18px 18px;
  opacity: 0.28;
  mix-blend-mode: soft-light;
}

.hero-glow-one {
  background: radial-gradient(circle at 28% 50%, rgba(255, 255, 255, 0.68), transparent 34%);
  animation: glowDriftOne 16s ease-in-out infinite;
}

.hero-glow-two {
  background: radial-gradient(circle at 72% 38%, rgba(255, 255, 255, 0.36), transparent 28%);
  animation: glowDriftTwo 18s ease-in-out infinite;
}

.hero-inner {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 56px;
  align-items: center;
  min-height: 100%;
  padding: 8vh 7vw;
}

.hero-orb-wrap {
  display: grid;
  place-items: center;
}

.cloudcycle-orb {
  position: relative;
  width: min(26vw, 260px);
  aspect-ratio: 1;
  border-radius: 50%;
  animation: orbFloat 8s ease-in-out infinite;
}

.orb-core,
.orb-ring,
.orb-glow,
.orb-reflection,
.orb-spark {
  position: absolute;
  inset: 0;
  border-radius: 50%;
}

.orb-core {
  background:
    radial-gradient(circle at 30% 28%, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.24) 18%, transparent 24%),
    radial-gradient(circle at 70% 72%, rgba(255, 173, 111, 0.42), transparent 30%),
    radial-gradient(circle at 72% 28%, rgba(55, 220, 199, 0.38), transparent 26%),
    linear-gradient(150deg, #6ca7ff 0%, #47d6cb 58%, #ffb88b 100%);
  box-shadow:
    inset -22px -28px 36px rgba(0, 0, 0, 0.14),
    inset 20px 20px 30px rgba(255, 255, 255, 0.32),
    0 44px 90px rgba(61, 117, 214, 0.28);
}

.orb-ring {
  border: 1px solid rgba(255, 255, 255, 0.42);
}

.orb-ring-one {
  transform: scale(1.12);
  animation: ringSpin 16s linear infinite;
}

.orb-ring-two {
  transform: scale(1.24);
  opacity: 0.28;
  animation: ringSpinReverse 20s linear infinite;
}

.orb-glow {
  inset: -34px;
  background: radial-gradient(circle, rgba(113, 180, 255, 0.22), transparent 62%);
  filter: blur(12px);
}

.orb-reflection {
  inset: 20px 56px auto 40px;
  height: 62px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0));
  transform: rotate(-16deg);
  opacity: 0.92;
}

.orb-spark {
  inset: auto 28px 34px auto;
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.88);
  filter: blur(1px);
  box-shadow: 0 0 24px rgba(255, 255, 255, 0.74);
  animation: sparkPulse 3.4s ease-in-out infinite;
}

.hero-copy {
  max-width: 860px;
}

.hero-mark,
.hero-subtitle {
  margin: 0;
}

.hero-mark {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(17, 39, 76, 0.52);
}

.hero-copy h1 {
  margin: 18px 0 18px;
  min-height: 2.3em;
  font-size: clamp(42px, 5.6vw, 84px);
  line-height: 1.02;
  letter-spacing: -0.05em;
  color: #10213f;
}

.typing-caret {
  display: inline-block;
  width: 0.08em;
  height: 0.9em;
  margin-left: 0.08em;
  vertical-align: -0.08em;
  background: currentColor;
  animation: caretBlink 1s steps(1) infinite;
}

.hero-subtitle {
  min-height: 4em;
  max-width: 760px;
  font-size: clamp(16px, 1.55vw, 22px);
  line-height: 1.9;
  color: rgba(16, 33, 63, 0.7);
}

.hero-mode-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}

.mode-chip {
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: rgba(16, 33, 63, 0.62);
  background: rgba(255, 255, 255, 0.62);
  box-shadow: inset 0 0 0 1px rgba(17, 39, 73, 0.06);
  transition: all 0.45s ease;
}

.mode-chip.active {
  color: #14305a;
  background:
    linear-gradient(135deg, rgba(76, 132, 255, 0.18), rgba(47, 211, 193, 0.18)),
    rgba(255, 255, 255, 0.78);
}

.enter-btn {
  margin-top: 34px;
  border: none;
  border-radius: 999px;
  padding: 16px 26px;
  background: linear-gradient(135deg, #4d86ff, #35d1c2);
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 22px 44px rgba(53, 114, 220, 0.24);
  transition:
    transform 0.35s ease,
    box-shadow 0.35s ease,
    background 0.45s ease;
}

.enter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 30px 50px rgba(53, 114, 220, 0.28);
}

@keyframes caretBlink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}

@keyframes orbFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

@keyframes ringSpin {
  from { transform: scale(1.12) rotate(0deg); }
  to { transform: scale(1.12) rotate(360deg); }
}

@keyframes ringSpinReverse {
  from { transform: scale(1.24) rotate(0deg); }
  to { transform: scale(1.24) rotate(-360deg); }
}

@keyframes sparkPulse {
  0%, 100% { transform: scale(0.92); opacity: 0.72; }
  50% { transform: scale(1.14); opacity: 1; }
}

@keyframes glowDriftOne {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(2%, 4%, 0); }
}

@keyframes glowDriftTwo {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(-3%, 3%, 0); }
}

@media (max-width: 980px) {
  .hero-inner {
    grid-template-columns: 1fr;
    gap: 28px;
    padding: 8vh 8vw 10vh;
  }

  .hero-orb-wrap {
    justify-content: start;
  }

  .cloudcycle-orb {
    width: min(52vw, 220px);
  }
}

</style>

<style>
[data-theme='dark'] .intro-hero {
  background:
    radial-gradient(circle at 14% 18%, rgba(85, 126, 255, 0.34), transparent 28%),
    radial-gradient(circle at 84% 22%, rgba(74, 192, 179, 0.22), transparent 26%),
    radial-gradient(circle at 50% 82%, rgba(255, 170, 110, 0.12), transparent 20%),
    linear-gradient(180deg, rgba(5, 10, 22, 0.98), rgba(10, 17, 33, 0.94));
}

[data-theme='dark'] .intro-hero .hero-mark,
[data-theme='dark'] .intro-hero .hero-subtitle,
[data-theme='dark'] .intro-hero .mode-chip {
  color: rgba(236, 244, 255, 0.68);
}

[data-theme='dark'] .intro-hero .hero-copy h1 {
  color: #edf4ff;
}

[data-theme='dark'] .intro-hero .mode-chip {
  background: rgba(255, 255, 255, 0.06);
}

[data-theme='dark'] .intro-hero .mode-chip.active {
  color: #edf4ff;
  background:
    linear-gradient(135deg, rgba(64, 117, 255, 0.24), rgba(41, 187, 173, 0.18)),
    rgba(255, 255, 255, 0.08);
}
</style>
