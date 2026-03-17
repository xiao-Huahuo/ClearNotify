import axios from 'axios';

// API 路径常量
export const API_ROUTES = {
  LOGIN: '/login/',
  REGISTER: '/user',
  GET_ME: '/user/me',
  CHAT_MESSAGE: '/chat/', // 对应后端 main.py 中 prefix="/chat"
  ANALYSIS_ME: '/analysis/me',
  SETTINGS_ME: '/settings/me', // 新增设置接口
};

// 统一的 API Client
export const apiClient = axios.create({
  baseURL: '/api', // 这里使用 /api，通过 Vite 代理转发到后端
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：自动附加 Token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});
