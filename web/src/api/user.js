import { apiClient, API_ROUTES } from '@/router/api_routes';

export const login = (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  return apiClient.post(API_ROUTES.LOGIN, params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
};

export const register = (userData) => {
  return apiClient.post(API_ROUTES.REGISTER, userData);
};

export const verifyEmail = (email, code) => {
  return apiClient.post(API_ROUTES.VERIFY_EMAIL, { email, code });
};

export const resendVerification = (email) => {
  return apiClient.post(API_ROUTES.RESEND_VERIFICATION, { email });
};

export const getMe = (token) => {
  return apiClient.get(API_ROUTES.GET_ME, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};
