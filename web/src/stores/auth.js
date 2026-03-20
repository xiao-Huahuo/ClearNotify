import { defineStore } from 'pinia';
import { ref } from 'vue';
import { login as loginApi, getMe } from '@/api/user';

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || null);
  const user = ref(null);

  const setToken = (newToken) => {
    token.value = newToken;
    localStorage.setItem('token', newToken);
  };

  const fetchUser = async () => {
    if (token.value) {
      try {
        const response = await getMe(token.value);
        user.value = response.data;
      } catch (error) {
        console.error('Failed to fetch user:', error);
        // Token 失效，清除
        token.value = null;
        user.value = null;
        localStorage.removeItem('token');
      }
    }
  };

  const login = async (username, password) => {
    const response = await loginApi(username, password);
    setToken(response.data.access_token);
    await fetchUser();
  };

  const logout = () => {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
  };

  return { token, user, login, logout, fetchUser };
});
