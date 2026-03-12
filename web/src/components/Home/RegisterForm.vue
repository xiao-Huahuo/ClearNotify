<template>
  <div class="register-form">
    <h2>Register</h2>
    <form @submit.prevent="handleRegister">
      <div>
        <label>Username:</label>
        <input v-model="username" type="text" required />
      </div>
      <div>
        <label>Email:</label>
        <input v-model="email" type="email" required />
      </div>
      <div>
        <label>Password:</label>
        <input v-model="password" type="password" required />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Registering...' : 'Register' }}
      </button>
      <div v-if="errorMessage" class="error">{{ errorMessage }}</div>
    </form>
    <div class="switch-link">
      Already have an account?
      <a href="#" @click.prevent="$emit('switch-to-login')">Login</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { register } from '@/api/user';

const emit = defineEmits(['success', 'switch-to-login']);

const username = ref('');
const email = ref('');
const password = ref('');
const errorMessage = ref('');
const loading = ref(false);

const handleRegister = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    await register({
      uname: username.value,
      email: email.value,
      pwd: password.value,
    });
    alert('Registration successful! Please login.');
    emit('switch-to-login');
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Registration failed';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-form {
  padding: 20px;
}
input {
  width: 100%;
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
button {
  width: 100%;
  padding: 10px;
  background-color: #008CBA;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}
button:disabled {
  background-color: #81d4fa;
  cursor: not-allowed;
}
.error {
  color: red;
  margin-top: 10px;
  font-size: 14px;
}
.switch-link {
  margin-top: 15px;
  text-align: center;
  font-size: 14px;
}
.switch-link a {
  color: #2196F3;
  text-decoration: none;
}
</style>
