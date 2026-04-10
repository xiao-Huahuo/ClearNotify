<template>
  <section class="footer-section" :class="{ ready }">
    <div class="section-shell">
      <div class="footer-panel">
        <div class="footer-brand">
          <span class="brand-tag">云上观策</span>
          <h2>用一套真正现代的首页，结束这次重构。</h2>
          <p>
            现在首页已经拥有整屏切换、统一组件边界、动态视觉叙事与真实接口支撑。
            接下来用户看到的将不再是“能用就行”，而是“这产品真的做过设计”。
          </p>
        </div>

        <div class="footer-links">
          <button v-for="link in footerLinks" :key="link.route" class="footer-link" @click="router.push(link.route)">
            {{ link.label }}
          </button>
        </div>

        <div class="footer-bottom">
          <span>© 2026 云上观策. All rights reserved.</span>
          <button class="back-top" @click="emitShowcaseGoto(0)">回到顶部</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { footerLinks } from './showcaseContent'
import { emitShowcaseGoto, showcaseSectionProps, useSectionReady } from './useShowcaseSection'

defineOptions({ name: 'FooterSection' })
defineProps(showcaseSectionProps)

const router = useRouter()
const ready = useSectionReady()
</script>

<style scoped>
.footer-section {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at left top, rgba(255, 141, 113, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(9, 12, 19, 0.98), rgba(4, 6, 10, 1));
  color: #fff;
}

.section-shell {
  height: 100%;
  padding: 112px 6vw 44px;
  display: grid;
  place-items: center;
}

.footer-panel {
  width: min(1040px, 100%);
  padding: 42px;
  border-radius: 34px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 34px 80px rgba(0, 0, 0, 0.32);
  opacity: 0;
  transform: translateY(26px);
  transition: opacity 0.82s var(--showcase-ease), transform 0.82s var(--showcase-ease);
}

.footer-section.ready .footer-panel {
  opacity: 1;
  transform: translateY(0);
}

.brand-tag {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.74);
  font-size: 12px;
  letter-spacing: 0.2em;
}

.footer-brand h2 {
  margin: 20px 0 12px;
  font-family: 'STZhongsong', 'Songti SC', 'Noto Serif SC', serif;
  font-size: clamp(32px, 3.8vw, 54px);
  line-height: 1.15;
}

.footer-brand p {
  max-width: 760px;
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  line-height: 1.84;
}

.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 30px;
}

.footer-link,
.back-top {
  height: 46px;
  padding: 0 20px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  cursor: pointer;
  transition: transform 0.3s var(--showcase-ease), background 0.3s ease;
}

.footer-link:hover,
.back-top:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.12);
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-top: 34px;
  padding-top: 22px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}

@media (max-width: 768px) {
  .section-shell {
    padding: 88px 20px 28px;
  }

  .footer-panel {
    padding: 28px 22px;
  }

  .footer-bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
