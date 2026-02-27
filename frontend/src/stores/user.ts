import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import {Auth, Users} from "@/api";

type User = {
    username: string;
    email: string;
    id: number;
    is_superuser: boolean;
}

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  if (localStorage.getItem("user")) {
    user.value = JSON.parse(localStorage.getItem("user") as string)
  }

  // Getters
  const isAuthenticated = computed(() => !!user.value);
  const userProfile = computed(() => user.value);

  // Actions
  async function authLogin(username: string, password: string) {
    loading.value = true;
    error.value = null;
    try {
      const {error: authError} = await Auth.authSessionLogin({
        body: {
          username,
          password
        }
      });

      if (authError) {
        console.error('Auth login failed:', authError);
        error.value = 'Invalid username or password';
        return false;
      }

      const {data: userData, error: userError} = await Users.usersMe();
      if (userError) {
        console.error('Failed to fetch user profile:', userError);
        error.value = 'Failed to fetch user profile';
        return false;
      }

      user.value = userData as any;
      localStorage.setItem("user", JSON.stringify(userData));

      return true;
    } catch (err) {
      console.error('Auth login failed:', err);
      error.value = 'Invalid username or password';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function logout() {
    try {
      await Auth.authSessionLogout();
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      user.value = null;
      localStorage.removeItem('auth_token');
      localStorage.removeItem("user")
    }
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
    authLogin,
    logout,
  };
});
