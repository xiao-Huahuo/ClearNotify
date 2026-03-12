<template>
  <div class="home-container">
    <!-- 标题区域 (始终显示，或者在结果页也可以显示，视情况而定，这里先始终显示) -->
    <div class="hero-section" v-if="!showResult">
      <h1 class="main-title">文档解析</h1>
      <p class="sub-title">全格式兼容-精准提取-详细输出</p>
    </div>

    <!-- 初始视图：上传区 + 示例区 -->
    <div v-if="!showResult" class="initial-view">
      <!-- 上传区域 -->
      <div
        class="upload-area"
        @click="triggerFileUpload"
        @dragover.prevent
        @drop.prevent="handleDrop"
        :class="{ 'disabled': loading }"
      >
        <div class="upload-buttons">
          <button class="action-btn" @click.stop="triggerFileUpload" :disabled="loading">
            <span class="icon">📂</span> 本地上传
          </button>
          <button class="action-btn" @click.stop="handleUrlUpload" :disabled="loading">
            <span class="icon">🔗</span> URL上传
          </button>
          <button class="action-btn" @click.stop="handleScreenshot" :disabled="loading">
            <span class="icon">📷</span> 截图
          </button>
        </div>
        <p class="upload-hint">点击或拖拽上传</p>

        <!-- 隐藏的文件输入框 -->
        <input
          type="file"
          ref="fileInput"
          style="display: none"
          @change="handleFileUpload"
        />
      </div>

      <!-- 加载中小横幅 -->
      <div v-if="loading" class="loading-banner">
        <div class="spinner"></div>
        <span>正在智能解读中...</span>
      </div>

      <!-- 示例区域 -->
      <div class="examples-section">
        <h2 class="section-title">示例</h2>
        <div class="examples-grid">
          <div v-for="ex in examples" :key="ex.id" class="example-card">
            <div class="card-image">
              <div class="placeholder-img">IMG</div>
            </div>
            <div class="card-content">
              <h3 class="card-title">{{ ex.title }}</h3>
              <div class="card-tags">
                <span v-for="tag in ex.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 结果视图 -->
    <div v-else class="result-view">
      <div class="result-header">
        <button @click="resetView" class="back-btn">
          <span class="icon">←</span> 返回
        </button>
        <h2>解读结果</h2>
      </div>

      <div class="response-section">
        <div class="result-content">{{ aiResponse }}</div>
      </div>
    </div>

    <!-- 弹窗 -->
    <Modal :isOpen="showModal" @close="closeModal">
      <LoginForm
        v-if="currentForm === 'login'"
        @success="handleLoginSuccess"
        @switch-to-register="currentForm = 'register'"
      />
      <RegisterForm
        v-if="currentForm === 'register'"
        @switch-to-login="currentForm = 'login'"
        @success="currentForm = 'login'"
      />
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import { chatWithAI } from '@/api/ai';
import Modal from '@/components/common/Modal.vue';
import LoginForm from '@/components/Home/LoginForm.vue';
import RegisterForm from '@/components/Home/RegisterForm.vue';

const userStore = useUserStore();
const inputText = ref('');
const aiResponse = ref('');
const loading = ref(false);
const showResult = ref(false);
const fileInput = ref(null);

const showModal = ref(false);
const currentForm = ref('login');

const examples = ref([
  { id: 1, title: '社区通知', tags: ['通知', '民生', '公告'] },
  { id: 2, title: '政务文件', tags: ['政策', '解读', '官方'] },
  { id: 3, title: '学校通知', tags: ['教育', '学生', '家长'] },
]);

onMounted(() => {
  if (userStore.token) {
    userStore.fetchUser();
  }
});

const openLoginModal = () => {
  currentForm.value = 'login';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const handleLoginSuccess = () => {
  closeModal();
};

const triggerFileUpload = () => {
  if (loading.value) return;
  fileInput.value.click();
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  processFile(file);
};

const handleDrop = (event) => {
  if (loading.value) return;
  const file = event.dataTransfer.files[0];
  processFile(file);
};

const processFile = (file) => {
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      inputText.value = e.target.result;
      // 读取完成后直接提交
      submitToAI();
    };
    reader.readAsText(file);
  }
};

const handleUrlUpload = () => {
  if (loading.value) return;
  const url = prompt("请输入 URL:");
  if (url) {
    inputText.value = `URL: ${url}`;
    submitToAI();
  }
};

const handleScreenshot = () => {
  alert("截图功能开发中...");
};

const submitToAI = async () => {
  if (!userStore.token) {
    openLoginModal();
    return;
  }

  if (!inputText.value.trim()) {
    // 应该不会发生，因为只有有内容才调这个
    return;
  }

  loading.value = true;
  aiResponse.value = '';

  try {
    const response = await chatWithAI(inputText.value);
    aiResponse.value = response.data.reply;
    showResult.value = true;
  } catch (error) {
    console.error(error);
    if (error.response?.status === 401) {
       userStore.logout();
       openLoginModal();
    } else {
       alert('AI 服务暂时不可用: ' + (error.response?.data?.detail || error.message));
    }
  } finally {
    loading.value = false;
  }
};

const resetView = () => {
  inputText.value = '';
  aiResponse.value = '';
  showResult.value = false;
  if (fileInput.value) {
    fileInput.value.value = ''; // 清空文件选择
  }
};
</script>

<style scoped>
.home-container {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 标题区域 */
.hero-section {
  margin-bottom: 30px;
}
.main-title {
  font-size: 32px;
  font-weight: bold;
  color: #000;
  margin: 0 0 10px 0;
  letter-spacing: 2px;
}
.sub-title {
  font-size: 16px;
  color: #999;
  margin: 0;
}

/* 上传区域 */
.upload-area {
  background-color: #fff;
  border: 2px dashed #e0e0e0;
  border-radius: 20px;
  padding: 120px 60px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px; /* 减小一点，给 banner 留空间 */
}
.upload-area:hover {
  border-color: var(--color-middle);
  background-color: #fafafa;
}
.upload-area.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}
.upload-buttons {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-bottom: 20px;
}
.action-btn {
  background-color: #f5f5f5;
  border: none;
  border-radius: 12px;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: bold;
  color: #333;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.action-btn:hover {
  background-color: #eee;
  transform: translateY(-2px);
}
.upload-hint {
  font-size: 14px;
  color: #999;
  margin: 0;
}

/* 加载横幅 */
.loading-banner {
  background-color: #e6fffa;
  border: 1px solid var(--color-secondary);
  color: var(--color-text-dark);
  padding: 15px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 40px;
  animation: fadeIn 0.5s;
}
.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(0, 226, 220, 0.3);
  border-radius: 50%;
  border-top-color: var(--color-secondary);
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 示例区域 */
.examples-section {
  margin-top: 20px;
}
.section-title {
  font-size: 16px;
  color: #000;
  margin-bottom: 20px;
  font-weight: bold;
}
.examples-grid {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}
.example-card {
  flex: 1;
  min-width: 250px;
  max-width: 350px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #eee;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s;
  cursor: pointer;
}
.example-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.05);
}
.card-image {
  height: 140px;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ccc;
}
.card-content {
  padding: 15px;
  background-color: #fff;
  flex: 1;
}
.card-title {
  font-size: 16px;
  margin: 0 0 10px 0;
  color: #333;
}
.card-tags {
  display: flex;
  gap: 8px;
}
.tag {
  background-color: #f5f5f5;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #000;
}

/* 结果区域 */
.result-view {
  animation: fadeIn 0.5s;
}
.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}
.back-btn {
  background: none;
  border: 1px solid #ccc;
  padding: 8px 15px;
  border-radius: 20px;
  cursor: pointer;
  margin-right: 20px;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  transition: all 0.2s;
}
.back-btn:hover {
  background-color: #f0f0f0;
}
.response-section {
  padding: 30px;
  background-color: #fff;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  min-height: 300px;
}
.result-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #333;
}
</style>
