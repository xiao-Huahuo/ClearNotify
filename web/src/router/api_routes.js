import axios from 'axios';

// API 路径常量
export const API_ROUTES = {
  LOGIN: '/login/',
  REGISTER: '/user',
  GET_ME: '/user/me',
  CHAT_MESSAGE: '/chat/',
  ANALYSIS_ME: '/analysis/me',
  SETTINGS_ME: '/settings/me',
  UPLOAD_AVATAR: '/upload/avatar',
  UPLOAD_DOCUMENT: '/upload/document',
  UPLOAD_OCR: '/upload/ocr',
  NEWS_HOT: '/news/hot',
  NEWS_CENTRAL_DOCS: '/news/central-docs',
  NEWS_KEYWORDS: '/news/keywords',
  NEWS_SEARCH: '/news/search',
  NEWS_WITH_IMAGES: '/news/with-images',
  NEWS_DAILY_SUMMARY: '/news/daily-summary',
  TODO: '/todo/',
  TODO_FROM_CHAT: '/todo/from-chat',
  FAVORITE: '/favorite/',
  ADMIN_USERS: '/admin/users',
  ADMIN_STATS: '/admin/stats',
  ADMIN_ANALYSIS_ALL: '/admin/analysis/all',
  REQUEST_PERMISSION_UPGRADE: '/user/request-upgrade',
  REQUEST_PERMISSION_DOWNGRADE: '/user/request-downgrade',
};

// 统一的 API Client
export const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});

// 请求拦截器：自动附加 Token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
}, error => Promise.reject(error));
