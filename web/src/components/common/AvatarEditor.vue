<template>
  <div class="avatar-editor">
    <h3>选择或上传头像</h3>

    <!-- 当前头像预览 -->
    <div class="current-avatar-preview">
      <img :src="currentAvatarSrc" alt="Current Avatar" class="avatar-lg" />
    </div>

    <!-- 默认头像选择 -->
    <div class="default-avatars-grid">
      <div
        v-for="avatar in defaultAvatars"
        :key="avatar.name"
        class="default-avatar-item"
        :class="{ 'selected': selectedDefaultAvatar === avatar.path }"
        @click="selectDefaultAvatar(avatar.path)"
      >
        <img :src="avatar.path" :alt="avatar.name" class="avatar-sm" />
      </div>
    </div>

    <!-- 文件上传 -->
    <div class="upload-section">
      <input type="file" ref="fileInput" @change="handleFileUpload" accept="image/*" style="display: none;" />
      <button @click="triggerFileInput" class="action-btn outline">
        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21.2 15c.7-1.2 1-2.5.7-3.9-.6-3.1-4-5.4-7.5-5.4-3.3 0-6.4 2.1-7.7 5.1C2.8 11.5 2 13.8 2 16c0 2.2.8 4.2 2.1 5.8"></path><path d="M12 16v6"></path><path d="M15 19l-3 3-3-3"></path></svg>
        上传新头像
      </button>
      <span v-if="uploadingFile" class="file-name">{{ uploadingFile.name }}</span>
    </div>

    <div class="actions">
      <button @click="saveAvatar" class="action-btn primary" :disabled="isSaving">
        {{ isSaving ? '保存中...' : '保存' }}
      </button>
      <button @click="$emit('close')" class="action-btn">取消</button>
    </div>

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useUserStore } from '@/stores/auth.js';
import { apiClient, API_ROUTES } from '@/router/api_routes';

const emit = defineEmits(['close', 'saved']);

const userStore = useUserStore();
const fileInput = ref(null);
const uploadingFile = ref(null);
const selectedDefaultAvatar = ref(null);
const errorMessage = ref('');
const isSaving = ref(false);

// 默认头像列表，通过 Vite 的 import.meta.glob 动态导入
const defaultAvatars = ref([]);
const importDefaultAvatars = async () => {
  const modules = import.meta.glob('@/assets/photos/default-avatars/*.jpg', { eager: true });
  for (const path in modules) {
    const name = path.split('/').pop(); // 获取文件名
    defaultAvatars.value.push({
      name: name,
      path: modules[path].default // Vite 会处理成正确的 URL
    });
  }
};

onMounted(async () => {
  await importDefaultAvatars();
  // 初始化时，如果用户已有头像，判断是否是默认头像
  if (userStore.user?.avatar_url) {
    if (userStore.user.avatar_url.startsWith('default:')) {
      const defaultName = userStore.user.avatar_url.substring(8);
      const found = defaultAvatars.value.find(a => a.name === defaultName);
      if (found) {
        selectedDefaultAvatar.value = found.path;
      }
    } else {
      // 如果是上传的头像，则不选中任何默认头像
      selectedDefaultAvatar.value = null;
    }
  }
});

// 计算当前显示的头像源
const currentAvatarSrc = computed(() => {
  if (uploadingFile.value) {
    return URL.createObjectURL(uploadingFile.value);
  }
  if (selectedDefaultAvatar.value) {
    return selectedDefaultAvatar.value;
  }
  // 如果用户有头像，但不是默认头像，则显示用户上传的头像
  if (userStore.user?.avatar_url && !userStore.user.avatar_url.startsWith('default:')) {
    return userStore.user.avatar_url;
  }
  // 否则显示一个通用的默认头像
  if (defaultAvatars.value.length > 0) {
      return defaultAvatars.value[0].path;
  }
  return '';
});

const triggerFileInput = () => {
  if (fileInput.value) {
      fileInput.value.click();
  }
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    if (!file.type.startsWith('image/')) {
      errorMessage.value = '请选择图片文件。';
      uploadingFile.value = null;
      return;
    }
    if (file.size > 5 * 1024 * 1024) { // 5MB 限制
      errorMessage.value = '文件大小不能超过 5MB。';
      uploadingFile.value = null;
      return;
    }
    uploadingFile.value = file;
    selectedDefaultAvatar.value = null; // 上传新头像时取消选择默认头像
    errorMessage.value = '';
  }
};

const selectDefaultAvatar = (path) => {
  selectedDefaultAvatar.value = path;
  uploadingFile.value = null; // 选择默认头像时取消上传文件
  errorMessage.value = '';
};

const saveAvatar = async () => {
  isSaving.value = true;
  errorMessage.value = '';

  // 如果没有选择任何新头像，且没有上传文件，则不进行任何操作
  if (!uploadingFile.value && !selectedDefaultAvatar.value) {
      isSaving.value = false;
      emit('close');
      return;
  }

  try {
    let newAvatarUrl = "";

    if (uploadingFile.value) {
      // 1. 上传文件到后端
      const formData = new FormData();
      formData.append('file', uploadingFile.value);
      const uploadRes = await apiClient.post(API_ROUTES.UPLOAD_AVATAR, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      newAvatarUrl = uploadRes.data.avatar_url;
    } else if (selectedDefaultAvatar.value) {
      // 2. 如果选择了默认头像，构造其 URL
      const defaultName = selectedDefaultAvatar.value.split('/').pop();
      newAvatarUrl = `default:${defaultName}`;
    }

    // 3. 更新用户头像 URL 到后端
    await apiClient.patch(API_ROUTES.GET_ME, { avatar_url: newAvatarUrl });

    // 4. 更新 Pinia Store 中的用户数据
    userStore.user.avatar_url = newAvatarUrl;
    emit('saved'); // 通知父组件保存成功
    emit('close');
  } catch (error) {
    console.error('保存头像失败:', error);
    errorMessage.value = error.response?.data?.detail || '保存头像失败';
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.avatar-editor {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 10px;
}

.current-avatar-preview {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #eee;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f9f9f9;
}

.avatar-lg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-avatars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
  gap: 10px;
  width: 100%;
  max-width: 400px;
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 12px;
}

.default-avatar-item {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.default-avatar-item:hover {
  border-color: #ccc;
}

.default-avatar-item.selected {
  border-color: #000;
  box-shadow: 0 0 0 2px rgba(0,0,0,0.1);
}

.avatar-sm {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.file-name {
  font-size: 14px;
  color: #666;
}

.actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.action-btn {
  padding: 10px 25px;
  border-radius: 20px;
  font-size: 15px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #ddd;
  background-color: #fff;
  color: #333;
}

.action-btn.outline {
  background: transparent;
  border-color: #ccc;
  color: #666;
  display: flex;
  align-items: center;
  gap: 5px;
}

.action-btn.outline:hover {
  border-color: #000;
  color: #000;
}

.action-btn.primary {
  background-color: #000;
  color: #fff;
  border-color: #000;
}

.action-btn.primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #ff4d4f;
  margin-top: 15px;
  font-size: 14px;
}
</style>
