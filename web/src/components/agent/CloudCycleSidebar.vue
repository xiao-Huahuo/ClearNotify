<template>
  <div v-if="isMobile && open" class="sidebar-backdrop" @click="$emit('close')"></div>
  <aside
    class="cloudcycle-sidebar"
    :class="{ open, mobile: isMobile, closed: !open && !isMobile }"
  >
    <div class="sidebar-header">
      <div class="brand-block">
        <div class="brand-mark">CC</div>
        <div>
          <p class="brand-title">云小圆</p>
          <p class="brand-subtitle">CloudCycle Agent Center</p>
        </div>
      </div>
      <button
        v-if="isMobile"
        class="icon-btn"
        type="button"
        @click="$emit('close')"
      >
        收起
      </button>
    </div>

    <div class="sidebar-meta">
      <span class="status-pill" :class="connectionState">
        {{ connectionLabel }}
      </span>
    </div>

    <button class="new-conversation-btn" type="button" @click="$emit('create')">
      新建对话
    </button>

    <div class="conversation-list">
      <button
        v-for="item in conversations"
        :key="item.id"
        class="conversation-card"
        :class="{ active: item.id === activeConversationId }"
        type="button"
        @click="$emit('select', item.id)"
      >
        <div class="conversation-main">
          <span class="conversation-title">{{ item.title || '未命名对话' }}</span>
          <span class="conversation-time">{{ formatTime(item.updated_time) }}</span>
        </div>
        <button
          class="delete-btn"
          type="button"
          title="删除对话"
          @click.stop="$emit('delete', item.id)"
        >
          删除
        </button>
      </button>

      <div v-if="!conversations.length" class="empty-state">
        <p>还没有历史会话</p>
        <span>新建一个对话，开始让云小圆处理任务。</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  open: { type: Boolean, default: true },
  isMobile: { type: Boolean, default: false },
  isDark: { type: Boolean, default: false },
  connectionState: { type: String, default: 'disconnected' },
  activeConversationId: { type: Number, default: null },
  conversations: {
    type: Array,
    default: () => [],
  },
});

defineEmits(['create', 'select', 'delete', 'close']);

const connectionLabel = computed(() => {
  if (props.connectionState === 'ready') return '连接正常';
  if (props.connectionState === 'connecting') return '连接中';
  if (props.connectionState === 'error') return '连接异常';
  return '未连接';
});

const formatTime = (value) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return `${date.getMonth() + 1}.${String(date.getDate()).padStart(2, '0')} ${String(
    date.getHours()
  ).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};
</script>

<style scoped>
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(10, 18, 34, 0.24);
  backdrop-filter: blur(6px);
  z-index: 59;
}

.cloudcycle-sidebar,
.cloudcycle-sidebar * {
  transition-property: background, background-color, border-color, color, box-shadow, opacity, filter;
  transition-duration: 0.45s;
  transition-timing-function: ease;
}

.cloudcycle-sidebar {
  position: relative;
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 288px;
  padding: 22px 18px 18px;
  border-radius: 30px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.58)),
    linear-gradient(150deg, rgba(128, 173, 255, 0.14), rgba(255, 255, 255, 0));
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow:
    0 28px 60px rgba(14, 30, 62, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(18px);
  min-height: 0;
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

.cloudcycle-sidebar.closed {
  width: 0;
  padding-left: 0;
  padding-right: 0;
  margin-right: 0;
  opacity: 0;
  overflow: hidden;
  transform: translateX(-24px);
  pointer-events: none;
  border-color: transparent;
  box-shadow: none;
}

.cloudcycle-sidebar.mobile {
  position: fixed;
  top: 12px;
  left: 12px;
  bottom: 12px;
  transform: translateX(-112%);
  transition: transform 0.32s ease;
  max-width: min(84vw, 320px);
}

.cloudcycle-sidebar.mobile.open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.18) 28%, transparent 30%),
    linear-gradient(160deg, #6aa6ff, #3ed3c4 55%, #ffb387);
  box-shadow:
    0 14px 30px rgba(65, 121, 220, 0.28),
    inset 0 1px 6px rgba(255, 255, 255, 0.62);
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.08em;
  display: grid;
  place-items: center;
}

.brand-title,
.brand-subtitle {
  margin: 0;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  color: #10213f;
}

.brand-subtitle {
  margin-top: 3px;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(16, 33, 63, 0.56);
}

.icon-btn,
.new-conversation-btn,
.delete-btn {
  border: none;
  cursor: pointer;
}

.icon-btn {
  border-radius: 999px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.72);
  color: #24416e;
  font-size: 12px;
}

.sidebar-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-pill {
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #24416e;
  background: rgba(255, 255, 255, 0.62);
}

.status-pill.ready {
  color: #0a775c;
  background: rgba(83, 214, 174, 0.18);
}

.status-pill.connecting {
  color: #8a5c11;
  background: rgba(255, 196, 90, 0.18);
}

.status-pill.error {
  color: #a63838;
  background: rgba(255, 120, 120, 0.18);
}

.new-conversation-btn {
  width: 100%;
  padding: 14px 16px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(76, 132, 255, 0.96), rgba(47, 211, 193, 0.92)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0));
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.04em;
  box-shadow: 0 22px 40px rgba(53, 116, 224, 0.22);
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.conversation-card {
  appearance: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 18px;
  outline: none;
  text-align: left;
  background: rgba(255, 255, 255, 0.62);
  color: #173159;
  transition: transform 0.24s ease, box-shadow 0.24s ease, background 0.24s ease;
}

.conversation-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 30px rgba(20, 43, 79, 0.1);
}

.conversation-card.active {
  background:
    linear-gradient(135deg, rgba(85, 136, 255, 0.18), rgba(57, 215, 194, 0.18)),
    rgba(255, 255, 255, 0.84);
  box-shadow: 0 20px 36px rgba(42, 88, 170, 0.16);
}

.conversation-card:focus-visible {
  box-shadow:
    0 0 0 2px rgba(77, 133, 255, 0.2),
    0 16px 30px rgba(20, 43, 79, 0.12);
}

.conversation-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.conversation-title {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-time {
  font-size: 11px;
  color: rgba(23, 49, 89, 0.56);
}

.delete-btn {
  flex-shrink: 0;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(14, 30, 62, 0.06);
  color: rgba(23, 49, 89, 0.72);
  font-size: 11px;
}

.empty-state {
  margin-top: 4px;
  padding: 18px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.52);
  color: rgba(23, 49, 89, 0.72);
}

.empty-state p,
.empty-state span {
  margin: 0;
  display: block;
}

.empty-state p {
  font-size: 14px;
  font-weight: 700;
}

.empty-state span {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.6;
}

:global([data-theme='dark']) .cloudcycle-sidebar {
  background:
    linear-gradient(180deg, rgba(11, 18, 35, 0.82), rgba(11, 18, 35, 0.66)),
    linear-gradient(150deg, rgba(70, 126, 255, 0.18), rgba(255, 255, 255, 0));
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow:
    0 30px 70px rgba(0, 0, 0, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

:global([data-theme='dark']) .brand-title,
:global([data-theme='dark']) .conversation-title {
  color: #eef4ff;
}

:global([data-theme='dark']) .brand-subtitle,
:global([data-theme='dark']) .conversation-time,
:global([data-theme='dark']) .empty-state,
:global([data-theme='dark']) .delete-btn,
:global([data-theme='dark']) .icon-btn {
  color: rgba(232, 241, 255, 0.72);
}

:global([data-theme='dark']) .status-pill,
:global([data-theme='dark']) .icon-btn,
:global([data-theme='dark']) .conversation-card,
:global([data-theme='dark']) .empty-state,
:global([data-theme='dark']) .delete-btn {
  background: rgba(255, 255, 255, 0.06);
}

:global([data-theme='dark']) .conversation-card.active {
  background:
    linear-gradient(135deg, rgba(63, 118, 255, 0.22), rgba(44, 196, 179, 0.18)),
    rgba(255, 255, 255, 0.08);
}
</style>
