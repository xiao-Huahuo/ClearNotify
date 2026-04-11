import { apiClient, API_ROUTES } from '@/router/api_routes';
import { serializeSearchTypes } from '@/utils/unifiedSearch';

const buildSearchParams = (q, limit, extraParams = {}) => {
  const params = { q, limit, ...extraParams };
  const serializedTypes = serializeSearchTypes(extraParams.types);
  if (serializedTypes) params.types = serializedTypes;
  else delete params.types;
  return params;
};

export const unifiedSearch = (q, limit = 20, extraParams = {}) =>
  apiClient.get(API_ROUTES.SEARCH_UNIFIED, {
    params: buildSearchParams(q, limit, extraParams),
  });

export const getSearchSuggestions = (q = '', limit = 18, extraParams = {}) =>
  apiClient.get(API_ROUTES.SEARCH_SUGGEST, {
    params: buildSearchParams(q, limit, extraParams),
  });

export const getSearchSuggestIndex = (limit = 240, extraParams = {}) =>
  apiClient.get(API_ROUTES.SEARCH_SUGGEST_INDEX, {
    params: { limit, ...extraParams },
  });
