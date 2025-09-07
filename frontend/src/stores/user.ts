import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { loginReq, type LoginResponse } from '@/api/auth';
import VueJwtDecode from 'vue-jwt-decode';

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<LoginResponse['user'] | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  if (localStorage.getItem("user")) {
    user.value = JSON.parse(localStorage.getItem("user") as string)
  }

  // Getters
  const isAuthenticated = computed(() => !!user.value);
  const userProfile = computed(() => user.value);

  // Actions
  async function login(email: string, password: string) {
    loading.value = true;
    error.value = null;

    try {
      const data = await loginReq(email, password) as LoginResponse;
      const { access_token, token_type } = data;

        // Decode JWT token to get user information
        const decoded = VueJwtDecode.decode(access_token)
        const responseUser = {
            username: decoded.sub,
            email: decoded.user.email,
            id: decoded.user.id,
            is_superuser: decoded.user.is_superuser
        }
        user.value = responseUser;

      localStorage.setItem('auth_token', access_token);
      localStorage.setItem("user", JSON.stringify(responseUser))

      return true;
    } catch (err) {
      console.error('Login failed:', err);
      error.value = 'Invalid email or password';
      return false;
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    user.value = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem("user")
  }

  return {
    // State
    user,
    loading,
    error,

    // Getters
    isAuthenticated,
    userProfile,

    // Actions
    login,
    logout,
  };
});
