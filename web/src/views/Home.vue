<template>
  <div class="home-container">
    <!-- 标题区域 -->
    <div class="hero-section">
      <h1 class="main-title">文档解析</h1>
      <p class="sub-title">全格式兼容-精准提取-详细输出</p>
    </div>

    <!-- 上传区域 -->
    <div
      class="upload-area"
      @click="triggerFileUpload"
      @dragover.prevent
      @drop.prevent="handleDrop"
    >
      <div class="upload-buttons">
        <button class="action-btn" @click.stop="triggerFileUpload">
          <span class="icon">📂</span> 本地上传
        </button>
        <button class="action-btn" @click.stop="handleUrlUpload">
          <span class="icon">🔗</span> URL上传
        </button>
        <button class="action-btn" @click.stop="handleScreenshot">
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

    <!-- 提交按钮 (如果已上传内容) -->
    <div v-if="inputText" class="submit-area">
      <p class="file-status">已准备好内容，点击下方按钮开始解读</p>
      <button @click="submitToAI" :disabled="loading" class="submit-btn">
        {{ loading ? '解读中...' : '开始智能解读' }}
      </button>
    </div>

    <!-- 示例区域 -->
    <div class="examples-section">
      <h2 class="section-title">示例</h2>
      <div class="examples-grid">
        <div v-for="ex in examples" :key="ex.id" class="example-card">
          <div class="card-image">
            <!-- 占位图片 -->
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

    <!-- 结果区域 -->
    <div v-if="aiResponse" class="response-section">
      <h3>解读结果：</h3>
      <div class="result-content">{{ aiResponse }}</div>
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
  fileInput.value.click();
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  processFile(file);
};

const handleDrop = (event) => {
  const file = event.dataTransfer.files[0];
  processFile(file);
};

const processFile = (file) => {
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      inputText.value = e.target.result;
      alert(`已加载文件: ${file.name}`);
    };
    reader.readAsText(file);
  }
};

const handleUrlUpload = () => {
  const url = prompt("请输入 URL:");
  if (url) {
    inputText.value = `URL: ${url}`; // 简单处理
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
    alert('请先上传文件或输入内容');
    return;
  }

  loading.value = true;
  aiResponse.value = '';

  try {
    const response = await chatWithAI(inputText.value);
    aiResponse.value = response.data.reply;
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
  font-size: 32px; /* 缩小三分之一 (48 -> 32) */
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
  padding: 120px 60px; /* 竖直方向增大一倍 (60 -> 120) */
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 40px;
}
.upload-area:hover {
  border-color: var(--color-middle);
  background-color: #fafafa;
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
  padding: 8px 20px; /* 纵向缩小，水平也缩小 (原来 15 30) */
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

/* 提交区域 */
.submit-area {
  text-align: center;
  margin-bottom: 40px;
}
.file-status {
  color: #666;
  margin-bottom: 15px;
}
.submit-btn {
  background-color: var(--sidebar-active-bg);
  border: 2px solid var(--sidebar-active-border);
  color: var(--color-text-dark);
  padding: 12px 40px;
  cursor: pointer;
  border-radius: 12px;
  font-size: 18px;
  font-weight: bold;
  transition: all 0.3s;
}
.submit-btn:hover {
  transform: translateY(-2px);
  background-color: #d1f7f5;
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
  max-width: 350px; /* 大约 1/3 */
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
  height: 140px; /* 控制高度比例 */
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
  border-radius: 6px; /* 圆角矩形 */
  font-size: 12px;
  color: #000;
}

/* 结果区域 */
.response-section {
  margin-top: 40px;
  padding: 30px;
  background-color: #fff;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
}
</style>
