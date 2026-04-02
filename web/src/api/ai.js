import { apiClient, API_ROUTES } from '@/router/api_routes';

export const createChatMessage = (original_text, parse_task_id = null) => {
  const params = parse_task_id ? { parse_task_id } : undefined;
  return apiClient.post(API_ROUTES.CHAT_MESSAGE, { original_text }, { params });
};

export const createChatMessageWithFile = (original_text, file_url, parse_task_id = null) => {
  const params = parse_task_id ? { parse_task_id } : undefined;
  return apiClient.post(API_ROUTES.CHAT_MESSAGE, {
    original_text,
    file_url,
  }, { params });
};

export const startChatProgressTask = () => {
  return apiClient.post(API_ROUTES.CHAT_PROGRESS_START);
};

export const uploadAndExtractDocument = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post(API_ROUTES.UPLOAD_DOCUMENT, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getChatMessages = (params = {}) => {
  return apiClient.get(API_ROUTES.CHAT_MESSAGE, { params });
};

export const getChatMessage = (id) => {
  return apiClient.get(`${API_ROUTES.CHAT_MESSAGE}${id}`);
};

export const rewriteChatMessage = (id, target_audience) => {
  return apiClient.patch(`${API_ROUTES.CHAT_MESSAGE}${id}`, { target_audience });
};

export const deleteChatMessage = (id) => {
  return apiClient.delete(`${API_ROUTES.CHAT_MESSAGE}${id}`);
};

export const batchDeleteChatMessages = (ids) => {
  return apiClient.post(`${API_ROUTES.CHAT_MESSAGE}batch-delete`, { message_ids: ids });
};

export const importChatMessage = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post(API_ROUTES.CHAT_IMPORT, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const exportChatMessage = (id) => {
  return apiClient.get(`${API_ROUTES.CHAT_MESSAGE}${id}/export`, {
    responseType: 'blob',
  });
};

export const openChatMessageFolder = (id) => {
  return apiClient.get(`${API_ROUTES.CHAT_MESSAGE}${id}/open-folder`);
};
