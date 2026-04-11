<template>
  <div class="favorites-container">
    <div class="header-section">
      <PolicyTitle title="我的收藏" />
    </div>

    <div v-if="loading" class="empty-state">加载中...</div>
    <div v-else-if="items.length === 0" class="empty-state">暂无收藏</div>

    <div v-else class="favorites-grid">
      <div v-for="(item, index) in items" :key="item.fav.id" class="favorite-card fade-in-up" :style="{ animationDelay: `${index * 60}ms` }">
        <div class="card-header">
          <h3 class="card-title">{{ item.message?.handling_matter || formatName(item.message?.original_text) }}</h3>
          <span class="card-time">{{ formatDate(item.fav.created_time) }}</span>
        </div>
        <div class="card-body">
          <p class="card-text">{{ formatPreview(item.message?.original_text) }}</p>
          <div class="card-tags">
            <span class="tag">{{ item.message?.chat_analysis?.notice_type || '文档' }}</span>
            <span class="tag subtle">{{ item.message?.target_audience || '未知对象' }}</span>
          </div>
        </div>
        <div class="card-actions">
          <button class="action-btn" @click="openDetail(item.message)">查看详情</button>
          <button class="star-btn" @click="handleRemoveFavorite($event, item.fav.id)">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="#f1c40f" stroke="#e6ac00" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import PolicyTitle from '@/components/common/PolicyTitle.vue';
import { useRouter } from 'vue-router';
import { apiClient, API_ROUTES } from '@/router/api_routes.js';
import { useUserStore } from '@/stores/auth.js';

const userStore = useUserStore();
const router = useRouter();
const loading = ref(true);
const items = ref([]);

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}`;
};

const formatName = (text) => {
  if (!text) return '未命名';
  const cleanText = text.replace(/\s+/g, ' ');
  return cleanText.length > 16 ? cleanText.substring(0, 16) + '...' : cleanText;
};

const formatPreview = (text) => {
  if (!text) return '暂无内容';
  const cleanText = text.replace(/\s+/g, ' ');
  return cleanText.length > 120 ? cleanText.substring(0, 120) + '...' : cleanText;
};

const fetchFavorites = async () => {
  if (!userStore.token) {
    alert('请先登录查看收藏');
    loading.value = false;
    return;
  }
  try {
    const favRes = await apiClient.get(API_ROUTES.FAVORITE);
    const favList = favRes.data || [];
    const messageTasks = favList.map((fav) =>
      apiClient.get(`${API_ROUTES.CHAT_MESSAGE}${fav.chat_message_id}`)
        .then(res => ({ fav, message: res.data }))
        .catch(() => ({ fav, message: null }))
    );
    items.value = await Promise.all(messageTasks);
  } catch (e) {
    console.error('获取收藏失败', e);
  } finally {
    loading.value = false;
  }
};

const removeFavorite = async (favId) => {
  try {
    await apiClient.delete(`${API_ROUTES.FAVORITE}${favId}`);
    items.value = items.value.filter(item => item.fav.id !== favId);
  } catch (e) {
    alert('取消收藏失败');
  }
};

const handleRemoveFavorite = (event, favId) => {
  const btn = event.currentTarget;
  btn.classList.add('star-popping');
  btn.addEventListener('animationend', () => removeFavorite(favId), { once: true });
};

const openDetail = async (message) => {
  if (!message?.id) return;
  try {
    const res = await apiClient.get(`${API_ROUTES.CHAT_MESSAGE}${message.id}`);
    sessionStorage.setItem('restoredChatMessage', JSON.stringify(res.data));
    router.push('/home');
  } catch (e) {
    alert('打开详情失败');
  }
};

onMounted(fetchFavorites);
</script>

<style scoped>
.favorites-container {
  padding: 16px 20px 24px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.header-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.empty-state {
  color: var(--text-secondary);
  padding: 48px 16px;
  text-align: center;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 18px;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
}

.favorite-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  border-top: 3px solid var(--color-primary);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  opacity: 0;
  box-shadow: 0 16px 34px color-mix(in srgb, var(--color-primary) 10%, transparent);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.favorite-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 22px 38px color-mix(in srgb, var(--color-primary) 14%, transparent);
  border-color: color-mix(in srgb, var(--color-primary) 16%, var(--border-color));
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.fade-in-up {
  animation: fadeInUp 0.4s ease both;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.card-title {
  font-size: 15px;
  margin: 0;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.45;
}

.card-time {
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.card-text {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.65;
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  background: color-mix(in srgb, var(--color-primary) 10%, var(--card-bg));
  color: var(--color-primary-dark);
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 700;
}

.tag.subtle {
  background: color-mix(in srgb, var(--border-color) 46%, var(--card-bg));
  color: var(--text-secondary);
}

.card-actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  margin-top: auto;
}

.action-btn {
  background: var(--color-primary);
  border: none;
  border-bottom: 3px solid var(--color-primary-dark);
  border-radius: 999px;
  color: #fff;
  padding: 7px 18px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--color-primary-light);
  border-bottom-color: var(--color-primary);
}

.star-btn {
  background: color-mix(in srgb, #f1c40f 10%, var(--card-bg));
  border: 1px solid color-mix(in srgb, #f1c40f 32%, var(--border-color));
  border-radius: 999px;
  cursor: pointer;
  padding: 6px 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.star-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 18px color-mix(in srgb, #f1c40f 18%, transparent);
}

@keyframes star-pop {
  0%   { transform: scale(1); opacity: 1; }
  50%  { transform: scale(1.6); opacity: 1; }
  100% { transform: scale(0.2); opacity: 0; }
}

.star-btn.star-popping {
  animation: star-pop 0.4s ease forwards;
}

@media (max-width: 768px) {
  .favorites-container {
    padding: 14px 14px 24px;
  }

  .favorites-grid {
    grid-template-columns: 1fr;
  }

  .favorite-card {
    padding: 16px;
  }

  .card-header {
    flex-direction: column;
  }

  .card-time {
    font-size: 12px;
  }

  .card-actions {
    flex-wrap: wrap;
  }

  .action-btn {
    flex: 1 1 auto;
    text-align: center;
  }
}
</style>
