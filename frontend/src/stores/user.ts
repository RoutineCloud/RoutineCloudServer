import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import VueJwtDecode from 'vue-jwt-decode';
import {Authentication} from "@/api";

type User = {
    username: string;
    email: string;
    id: string;
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
  async function login(email: string, password: string) {
    loading.value = true;
    error.value = null;

    try {
        const {data, error} = await Authentication.loginForAccessTokenApiOauthTokenPost({
            body: {
                grant_type: "password",
                username: email,
                password: password
            }
        })
      const { access_token,
          token_type,
          refresh_token,
          expires_in,
          refresh_expires_in
        } = data;

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
    console.log("logged out")
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
