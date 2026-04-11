import axios from 'axios';

// API 路径常量
export const API_ROUTES = {
  LOGIN: '/login/',
  REGISTER: '/user',
  VERIFY_EMAIL: '/user/verify-email',
  RESEND_VERIFICATION: '/user/resend-verification',
  GET_ME: '/user/me',
  CHAT_MESSAGE: '/chat/',
  CHAT_PROGRESS_START: '/chat/progress/start',
  CHAT_PROGRESS_STREAM: '/chat/progress/stream',
  CHAT_IMPORT: '/chat/import',
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
  NEWS_HOT_TAGS: '/news/hot-tags',
  SEARCH_UNIFIED: '/search/unified',
  SEARCH_SUGGEST: '/search/suggest',
  SEARCH_SUGGEST_INDEX: '/search/suggest-index',
  HISTORY_FEED: '/history/feed',
  HISTORY_FACETS: '/history/facets',
  HISTORY_TRACK: '/history/track',
  TODO: '/todo/',
  TODO_FROM_CHAT: '/todo/from-chat',
  FAVORITE: '/favorite/',
  ADMIN_SET_ROLE: (uid) => `/admin/users/${uid}/set-role`,
  ADMIN_TOGGLE_ADMIN: (uid) => `/admin/users/${uid}/toggle-admin`,
  ADMIN_USERS: '/admin/users',
  ADMIN_STATS: '/admin/stats',
  ADMIN_STATS_STREAM: '/admin/stats/stream',
  ADMIN_ANALYSIS_ALL: '/admin/analysis/all',
  ADMIN_LOGS: '/admin/logs',
  ADMIN_RAG_STATUS: '/admin/rag/status',
  ADMIN_RAG_SEARCH: '/admin/rag/search',
  SHOWCASE_PUBLIC_STATS: '/showcase/landing-stats',
  SHOWCASE_SCREEN_DATA: '/showcase/screen-data',
  AGENT_RUN: '/agent/run',
  AGENT_CONVERSATIONS: '/agent/conversations',
  AGENT_MESSAGES: (id) => `/agent/conversations/${id}/messages`,
  REQUEST_PERMISSION_UPGRADE: '/user/request-upgrade',
  REQUEST_PERMISSION_DOWNGRADE: '/user/request-downgrade',
  POLICY_DOCS_MY_STATS: '/policy-documents/my-stats',
  POLICY_DOCS_APPROVED: '/policy-documents/approved',
  POLICY_DOCS_MINE: '/policy-documents/mine',
  POLICY_DOCS_PENDING: '/policy-documents/pending',
  POLICY_DOC_CREATE: '/policy-documents/',
  POLICY_DOC_DETAIL: (id) => `/policy-documents/${id}`,
  POLICY_DOC_REVIEW: (id) => `/policy-documents/${id}/review`,
  POLICY_DOC_VIEW: (id) => `/policy-documents/${id}/view`,
  POLICY_DOC_LIKE: (id) => `/policy-documents/${id}/like`,
  ADMIN_OPINION_STATS: '/admin/opinion-stats',
  ADMIN_USER_ROLE_DIST: '/admin/user-role-dist',
  ADMIN_USER_GEO: '/admin/user-geo',
  POLICY_DOC_RECOMMEND: '/policy-documents/recommend',
  POLICY_DOC_RECOMMEND_ME: '/policy-documents/recommend/me',
  OPINIONS_CREATE: '/opinions/',
  OPINIONS_FEED: '/opinions/feed',
  OPINIONS_MINE: '/opinions/mine',
  OPINIONS_BY_DOC: (docId) => `/opinions/doc/${docId}`,
  OPINION_LIKE: (id) => `/opinions/${id}/like`,
};

// 统一的 API Client
export const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000, // 将超时时间增加到 60 秒
});

// 请求拦截器：自动附加 Token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
}, error => Promise.reject(error));
