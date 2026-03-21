<template>
  <div class="sidebar">
    <div class="logo">
      <img src="@/assets/photos/main-icon.png" alt="icon" class="logo-icon" v-if="hasIcon" @error="hasIcon = false" />
      ClearNotify
    </div>
    <nav>
      <router-link to="/" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        主页
      </router-link>
      <router-link to="/discovery-home" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        发现
      </router-link>
      <router-link to="/data-analysis-and-visualization" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
        数据分析
      </router-link>
      <router-link to="/history" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        会话历史
      </router-link>
      <router-link to="/favorites" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
        我的收藏
      </router-link>
      <router-link to="/todo" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
        办事进度
      </router-link>
      <router-link v-if="userStore.user?.is_admin" to="/admin" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        管理员
      </router-link>
      <router-link to="/profile" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        我的
      </router-link>
    </nav>

    <!-- 未登录时的登录 widget -->
    <div class="login-widget" v-if="!userStore.token">
      <p class="widget-title">登录即享</p>
      <ul class="widget-list">
        <li>- AI 秒级解析政务文件</li>
        <li>- 个性化通知推送</li>
        <li>- 专属数据分析报告</li>
        <li>- 智能追问与改写</li>
      </ul>
      <button class="widget-login-btn" @click="emitLogin">立即登录</button>
    </div>

    <div class="sidebar-footer">
      <!-- 更多按钮 -->
      <div class="more-wrap" ref="moreWrapRef">
        <button class="more-btn" @click="toggleMore" title="更多">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="5" r="1" fill="currentColor"></circle><circle cx="12" cy="12" r="1" fill="currentColor"></circle><circle cx="12" cy="19" r="1" fill="currentColor"></circle></svg>
          更多
        </button>

        <!-- 弹出菜单 -->
        <transition name="more-pop">
          <div class="more-menu" v-if="showMore">
            <div class="more-item" @click="showAbout = true; showMore = false">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              关于
            </div>
            <div class="more-item" @click="showPermission = true; showMore = false">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
              权限设置
            </div>
            <div class="more-item disabled">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
              接入API <span class="coming-soon">即将上线</span>
            </div>
            <div class="more-item" @click="showFaq = true; showMore = false">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              常见问题
            </div>
            <div class="more-divider"></div>
            <div class="more-item danger" @click="doNotClick">
              <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              不要点这个！
            </div>
          </div>
        </transition>
      </div>

      <router-link to="/settings" class="settings-btn" active-class="active" title="设置">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
      </router-link>
    </div>

    <!-- 关于弹窗 -->
    <div class="overlay" v-if="showAbout" @click.self="showAbout = false">
      <div class="dialog">
        <h3 class="dialog-title">关于 ClearNotify</h3>
        <p class="dialog-text"><strong>关于本平台</strong><br>ClearNotify 是一款面向普通市民的政务文件智能解析平台，致力于让每一份通知都清晰易懂。</p>
        <p class="dialog-text"><strong>关于我们</strong><br>我们是一支热爱技术与公共服务的小团队，相信科技可以让政务信息更加普惠。</p>
        <button class="dialog-close" @click="showAbout = false">关闭</button>
      </div>
    </div>

    <!-- 权限设置弹窗 -->
    <div class="overlay" v-if="showPermission" @click.self="showPermission = false">
      <div class="dialog">
        <h3 class="dialog-title">权限设置</h3>
        <div v-if="userStore.user?.is_admin">
          <p class="dialog-text">您当前是 <strong>管理员</strong>。</p>
          <button class="dialog-btn" @click="requestDowngrade">申请降级为普通用户</button>
        </div>
        <div v-else-if="userStore.token">
          <p class="dialog-text">您当前是 <strong>普通用户</strong>。如需提升权限，请向管理员发送申请邮件。</p>
          <button class="dialog-btn" @click="requestUpgrade">发送权限申请邮件</button>
        </div>
        <div v-else>
          <p class="dialog-text">请先登录后再进行权限设置。</p>
        </div>
        <button class="dialog-close" @click="showPermission = false">关闭</button>
      </div>
    </div>

    <!-- 常见问题弹窗 -->
    <div class="overlay" v-if="showFaq" @click.self="showFaq = false">
      <div class="dialog">
        <h3 class="dialog-title">常见问题</h3>
        <div class="faq-item"><strong>Q: 支持哪些文件格式？</strong><p>A: 支持 PDF、Word（.doc/.docx）、Excel、TXT 以及图片截图（OCR识别）。</p></div>
        <div class="faq-item"><strong>Q: 解析结果准确吗？</strong><p>A: 基于大语言模型，准确率较高，但建议结合原文核对重要信息。</p></div>
        <div class="faq-item"><strong>Q: 数据会被保存吗？</strong><p>A: 登录用户的解析记录会保存在会话历史中，可随时查看或删除。</p></div>
        <div class="faq-item"><strong>Q: 语音播报支持哪些语言？</strong><p>A: 目前支持普通话，后续将支持更多方言。</p></div>
        <button class="dialog-close" @click="showFaq = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useUserStore } from '@/stores/auth.js';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';

const hasIcon = ref(true);
const userStore = useUserStore();

const showMore = ref(false);
const showAbout = ref(false);
const showPermission = ref(false);
const showFaq = ref(false);
const moreWrapRef = ref(null);

const toggleMore = () => { showMore.value = !showMore.value; };

const emitLogin = () => { window.dispatchEvent(new CustomEvent('open-login-modal')); };

const doNotClick = () => {
  showMore.value = false;
  // 打开原神官网
  window.open('https://ys.mihoyo.com/', '_blank');
  // 触发下载
  const a = document.createElement('a');
  a.href = 'https://ys-api.mihoyo.com/event/download_porter/link/ys_cn/official/pc_backup316';
  a.download = '';
  a.target = '_blank';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

const requestUpgrade = async () => {
  try {
    await apiClient.post(API_ROUTES.REQUEST_PERMISSION_UPGRADE);
    alert('申请已发送，请等待管理员审核。');
  } catch (e) {
    alert('发送失败，请稍后重试。');
  }
};

const requestDowngrade = async () => {
  if (!confirm('确定要将自己降级为普通用户吗？')) return;
  try {
    await apiClient.post(API_ROUTES.REQUEST_PERMISSION_DOWNGRADE);
    alert('已申请降级，邮件已发送。');
  } catch (e) {
    alert('操作失败，请稍后重试。');
  }
};

const handleClickOutside = (e) => {
  if (moreWrapRef.value && !moreWrapRef.value.contains(e.target)) {
    showMore.value = false;
  }
};

onMounted(() => document.addEventListener('click', handleClickOutside));
onUnmounted(() => document.removeEventListener('click', handleClickOutside));
</script>

<style scoped>
.sidebar {
  width: 200px;
  background: linear-gradient(180deg, #c0392b 0%, #922b21 60%, #7f8c8d 100%);
  color: #fff;
  height: 100vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.sidebar::before {
  content: '';
  position: absolute;
  bottom: -30px;
  left: -40px;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
  pointer-events: none;
}
.sidebar::after {
  content: '';
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
  pointer-events: none;
}

.logo {
  padding: 20px;
  font-size: 18px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  letter-spacing: 1px;
  position: relative;
  z-index: 1;
}
.logo-icon { width: 24px; height: 24px; filter: brightness(0) invert(1); }

nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px 0;
  position: relative;
  z-index: 1;
}

.nav-item {
  padding: 10px 20px;
  color: rgba(255,255,255,0.75);
  text-decoration: none;
  transition: all 0.2s;
  border-radius: 10px;
  margin: 3px 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}
.nav-item:hover {
  background-color: rgba(255,255,255,0.12);
  color: #fff;
}
.nav-item.active {
  background-color: rgba(255,255,255,0.2);
  color: #fff;
  font-weight: bold;
  box-shadow: inset 3px 0 0 #fff;
}
.nav-item.active .nav-icon { color: #fff; }

/* 未登录 widget */
.login-widget {
  margin: 0 10px 10px;
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 12px 14px;
  position: relative;
  z-index: 1;
}
.widget-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}
.widget-list {
  margin: 0 0 10px;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.widget-list li {
  font-size: 11px;
  color: rgba(255,255,255,0.8);
  line-height: 1.4;
}
.widget-login-btn {
  width: 100%;
  background: #fff;
  color: #c0392b;
  border: none;
  border-radius: 20px;
  padding: 7px 0;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
}
.widget-login-btn:hover { opacity: 0.9; }

.sidebar-footer {
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

/* 更多按钮 */
.more-wrap { position: relative; }
.more-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(255,255,255,0.15);
  border: none;
  border-radius: 8px;
  color: rgba(255,255,255,0.85);
  font-size: 13px;
  font-weight: 600;
  padding: 6px 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.more-btn:hover { background: rgba(255,255,255,0.25); color: #fff; }

.more-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  min-width: 160px;
  overflow: hidden;
  z-index: 100;
}
.more-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  transition: background 0.15s;
}
.more-item:hover { background: #f5f5f5; }
.more-item.disabled { opacity: 0.5; cursor: not-allowed; }
.more-item.disabled:hover { background: none; }
.more-item.danger { color: #c0392b; font-weight: 600; }
.more-item.danger:hover { background: #fff0f0; }
.coming-soon {
  font-size: 10px;
  background: #eee;
  color: #999;
  padding: 1px 6px;
  border-radius: 10px;
  margin-left: auto;
}
.more-divider { height: 1px; background: #f0f0f0; margin: 2px 0; }

.more-pop-enter-active, .more-pop-leave-active { transition: all 0.2s cubic-bezier(0.4,0,0.2,1); }
.more-pop-enter-from, .more-pop-leave-to { opacity: 0; transform: translateY(8px) scale(0.96); }

.settings-btn {
  color: rgba(255,255,255,0.6);
  cursor: pointer;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.settings-btn:hover, .settings-btn.active { color: #fff; }

/* 弹窗 overlay */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dialog {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.dialog-title {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 700;
  color: #111;
}
.dialog-text {
  font-size: 14px;
  color: #444;
  line-height: 1.7;
  margin: 0 0 12px;
}
.dialog-btn {
  background: #c0392b;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 9px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 12px;
  transition: background 0.2s;
}
.dialog-btn:hover { background: #e74c3c; }
.dialog-close {
  display: block;
  margin-top: 8px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 7px 18px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: background 0.2s;
}
.dialog-close:hover { background: #f5f5f5; }
.faq-item { margin-bottom: 14px; }
.faq-item strong { font-size: 13px; color: #111; }
.faq-item p { margin: 4px 0 0; font-size: 13px; color: #555; line-height: 1.5; }
</style>
