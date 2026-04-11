import { apiClient, API_ROUTES } from '@/router/api_routes';

export const getHistoryFeed = (params = {}) =>
  apiClient.get(API_ROUTES.HISTORY_FEED, { params });

export const getHistoryFacets = () =>
  apiClient.get(API_ROUTES.HISTORY_FACETS);

export const trackHistoryEvent = (payload) =>
  apiClient.post(API_ROUTES.HISTORY_TRACK, payload);
