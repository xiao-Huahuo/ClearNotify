<template>
  <div v-if="isMobile && open" class="inspector-backdrop" @click="$emit('close')"></div>
  <aside class="inspector-panel" :class="{ open, mobile: isMobile, closed: !open && !isMobile }">
    <div class="inspector-header">
      <div>
        <p class="panel-eyebrow">Run Inspector</p>
        <h2>推理与工具轨迹</h2>
      </div>
      <button v-if="isMobile" class="close-btn" type="button" @click="$emit('close')">
        关闭
      </button>
    </div>

    <section class="summary-grid">
      <article class="summary-card">
        <span>运行模式</span>
        <strong>{{ runModeLabel }}</strong>
      </article>
      <article class="summary-card">
        <span>解析模式</span>
        <strong>{{ agentResult?.parse_mode || '等待结果' }}</strong>
      </article>
      <article class="summary-card">
        <span>工具调用</span>
        <strong>{{ toolCount }}</strong>
      </article>
      <article class="summary-card">
        <span>知识命中</span>
        <strong>{{ evidenceCount }}</strong>
      </article>
      <article class="summary-card">
        <span>置信度</span>
        <strong>{{ confidenceText }}</strong>
      </article>
      <article class="summary-card">
        <span>连接状态</span>
        <strong>{{ connectionLabel }}</strong>
      </article>
    </section>

    <section class="inspector-section">
      <div class="section-title">本轮摘要</div>
      <div class="summary-text">
        {{ agentResult?.summary || (loading ? '本轮正在运行，等待摘要生成…' : '发起一次对话后，这里会展示本轮摘要。') }}
      </div>
    </section>

    <section class="inspector-section">
      <div class="section-title">思考轨迹</div>
      <div v-if="thoughtEntries.length" class="timeline-list">
        <article v-for="item in thoughtEntries" :key="item.id" class="timeline-card">
          <div class="timeline-meta">
            <span>思考</span>
            <small>{{ item.time }}</small>
          </div>
          <p>{{ item.title }}</p>
        </article>
      </div>
      <div v-else class="placeholder-text">本轮还没有记录到思考轨迹。</div>
    </section>

    <section class="inspector-section">
      <div class="section-title">工具调用</div>
      <div v-if="toolEntries.length" class="timeline-list">
        <article v-for="item in toolEntries" :key="item.id" class="timeline-card">
          <div class="timeline-meta">
            <span>{{ item.title }}</span>
            <small>{{ item.time }}</small>
          </div>
          <p v-if="item.input"><strong>输入：</strong>{{ item.input }}</p>
          <p v-if="item.output"><strong>输出：</strong>{{ item.output }}</p>
        </article>
      </div>
      <div v-else class="placeholder-text">当前没有工具调用记录。</div>
    </section>

    <section class="inspector-section">
      <div class="section-title">知识命中</div>
      <div v-if="normalizedEvidence.length" class="evidence-list">
        <article v-for="(item, index) in normalizedEvidence" :key="`${item.title}-${index}`" class="evidence-card">
          <div class="evidence-head">
            <strong>{{ item.title }}</strong>
            <span>{{ item.scoreText }}</span>
          </div>
          <p>{{ item.snippet }}</p>
        </article>
      </div>
      <div v-else class="placeholder-text">本轮没有命中知识库证据。</div>
    </section>
  </aside>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  open: { type: Boolean, default: true },
  isMobile: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  runMode: { type: String, default: 'agent' },
  connectionState: { type: String, default: 'disconnected' },
  agentResult: { type: Object, default: null },
  traceTimeline: {
    type: Array,
    default: () => [],
  },
});

defineEmits(['close']);

const runModeLabel = computed(() => (props.runMode === 'chat' ? 'Chat' : 'Agent'));
const toolEntries = computed(() => props.traceTimeline.filter((item) => item.kind === 'tool'));
const thoughtEntries = computed(() => props.traceTimeline.filter((item) => item.kind === 'thought'));
const toolCount = computed(() => props.agentResult?.tool_calls?.length || toolEntries.value.length || 0);
const evidenceCount = computed(() => props.agentResult?.evidence?.length || 0);
const confidenceText = computed(() => {
  const value = props.agentResult?.confidence;
  return typeof value === 'number' ? `${Math.round(value * 100)}%` : '待生成';
});

const connectionLabel = computed(() => {
  if (props.connectionState === 'ready') return '已连接';
  if (props.connectionState === 'connecting') return '连接中';
  if (props.connectionState === 'error') return '异常';
  return '未连接';
});

const normalizedEvidence = computed(() =>
  (props.agentResult?.evidence || []).map((item) => ({
    title: item.title || item.source || item.category || '知识条目',
    snippet: item.snippet || item.content || '暂无片段',
    scoreText:
      typeof item.score === 'number' ? `相似度 ${item.score.toFixed(3)}` : '相似度待定',
  }))
);
</script>

<style scoped>
.inspector-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(10, 18, 34, 0.24);
  backdrop-filter: blur(6px);
  z-index: 59;
}

.inspector-panel,
.inspector-panel * {
  transition-property: background, background-color, border-color, color, box-shadow, opacity, filter;
  transition-duration: 0.45s;
  transition-timing-function: ease;
}

.inspector-panel {
  position: relative;
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 360px;
  min-height: 0;
  padding: 22px 18px 18px;
  border-radius: 30px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.6)),
    linear-gradient(150deg, rgba(131, 180, 255, 0.14), rgba(255, 255, 255, 0));
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow:
    0 28px 60px rgba(14, 30, 62, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(18px);
  overflow: auto;
  transition:
    transform 0.55s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.45s ease,
    width 0.45s ease,
    padding 0.45s ease,
    margin 0.45s ease,
    background 0.45s ease,
    border-color 0.45s ease,
    box-shadow 0.45s ease;
}

.inspector-panel.closed {
  width: 0;
  padding-left: 0;
  padding-right: 0;
  opacity: 0;
  overflow: hidden;
  transform: translateX(24px);
  pointer-events: none;
  border-color: transparent;
  box-shadow: none;
}

.inspector-panel.mobile {
  position: fixed;
  top: 12px;
  right: 12px;
  bottom: 12px;
  max-width: min(88vw, 380px);
  transform: translateX(112%);
  transition: transform 0.32s ease;
}

.inspector-panel.mobile.open {
  transform: translateX(0);
}

.inspector-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-eyebrow,
.inspector-header h2 {
  margin: 0;
}

.panel-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(17, 39, 76, 0.48);
}

.inspector-header h2 {
  margin-top: 6px;
  font-size: 20px;
  line-height: 1.2;
  color: #10213f;
}

.close-btn {
  border: none;
  border-radius: 999px;
  padding: 8px 12px;
  background: rgba(17, 39, 76, 0.06);
  color: #173159;
  cursor: pointer;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-card,
.timeline-card,
.evidence-card,
.summary-text {
  background: rgba(255, 255, 255, 0.62);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.58);
}

.summary-card {
  padding: 14px;
}

.summary-card span,
.summary-card strong {
  display: block;
}

.summary-card span {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(17, 39, 76, 0.46);
}

.summary-card strong {
  margin-top: 8px;
  font-size: 15px;
  color: #11274c;
}

.inspector-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: #14305a;
}

.summary-text,
.timeline-card,
.evidence-card {
  padding: 14px;
  color: #173159;
}

.summary-text,
.timeline-card p,
.evidence-card p,
.placeholder-text {
  font-size: 13px;
  line-height: 1.75;
}

.timeline-list,
.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.timeline-meta,
.evidence-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.timeline-meta span,
.evidence-head strong {
  font-size: 13px;
  font-weight: 700;
}

.timeline-meta small,
.evidence-head span {
  font-size: 11px;
  color: rgba(23, 49, 89, 0.56);
}

.timeline-card p,
.evidence-card p {
  margin: 10px 0 0;
  word-break: break-word;
  white-space: pre-wrap;
}

.placeholder-text {
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.52);
  color: rgba(23, 49, 89, 0.58);
}

:global([data-theme='dark']) .inspector-panel {
  background:
    linear-gradient(180deg, rgba(11, 18, 35, 0.84), rgba(11, 18, 35, 0.7)),
    linear-gradient(150deg, rgba(70, 126, 255, 0.16), rgba(255, 255, 255, 0));
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow:
    0 28px 66px rgba(0, 0, 0, 0.36),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

:global([data-theme='dark']) .panel-eyebrow,
:global([data-theme='dark']) .timeline-meta small,
:global([data-theme='dark']) .evidence-head span,
:global([data-theme='dark']) .placeholder-text {
  color: rgba(237, 244, 255, 0.58);
}

:global([data-theme='dark']) .inspector-header h2,
:global([data-theme='dark']) .summary-card strong,
:global([data-theme='dark']) .section-title,
:global([data-theme='dark']) .summary-text,
:global([data-theme='dark']) .timeline-card,
:global([data-theme='dark']) .evidence-card,
:global([data-theme='dark']) .close-btn {
  color: #edf4ff;
}

:global([data-theme='dark']) .summary-card,
:global([data-theme='dark']) .summary-text,
:global([data-theme='dark']) .timeline-card,
:global([data-theme='dark']) .evidence-card,
:global([data-theme='dark']) .placeholder-text,
:global([data-theme='dark']) .close-btn {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.06);
}
</style>
