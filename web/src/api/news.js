import { apiClient, API_ROUTES } from '@/router/api_routes';

export const getHotNews = (limit = 10) =>
  apiClient.get(API_ROUTES.NEWS_HOT, { params: { limit } });

export const getCentralDocs = (limit = 5) =>
  apiClient.get(API_ROUTES.NEWS_CENTRAL_DOCS, { params: { limit } });

export const getHotKeywords = () =>
  apiClient.get(API_ROUTES.NEWS_KEYWORDS);

export const searchNews = (q, limit = 20, extraParams = {}) =>
  apiClient.get(API_ROUTES.NEWS_SEARCH, { params: { q, limit, ...extraParams } });

export const getNewsWithImages = (limit = 5) =>
  apiClient.get(API_ROUTES.NEWS_WITH_IMAGES, { params: { limit } });

export const getDailySummary = () =>
  apiClient.get(API_ROUTES.NEWS_DAILY_SUMMARY);

export const getHotTags = (limit = 6) =>
  apiClient.get(API_ROUTES.NEWS_HOT_TAGS, { params: { limit } });
