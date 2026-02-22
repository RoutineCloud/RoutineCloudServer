import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import VueJwtDecode from 'vue-jwt-decode';
import {Auth, Oauth2, Users} from "@/api";

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
      return true;
    } catch (err) {
      console.error('Auth login failed:', err);
      error.value = 'Invalid username or password';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function handleCallback(code: string) {
    loading.value = true;
    error.value = null;
    try {
      const {data, error: tokenError} = await Oauth2.oauthToken({
        body: {
          grant_type: "authorization_code",
          client_id: "routine-web",
          code,
          redirect_uri: "http://localhost:3000/callback"
        }
      });

      if (tokenError) {
        console.error('Token exchange failed:', tokenError);
        error.value = 'Failed to exchange authorization code';
        return false;
      }

      const { access_token } = data;
      localStorage.setItem('auth_token', access_token);

      const decoded = VueJwtDecode.decode(access_token);
      let responseUser = { id: decoded.sub };
      user.value = responseUser as User;
      localStorage.setItem("user", JSON.stringify(responseUser));

      const {data: userData, error: userError} = await Users.usersMe();
      if (!userError) {
        responseUser = { id: decoded.sub, ...userData };
        user.value = responseUser as User;
        localStorage.setItem("user", JSON.stringify(responseUser));
      }
      return true;
    } catch (err) {
      console.error('Callback handling failed:', err);
      error.value = 'Network error during callback';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function login(email: string, password: string) {
    // This old login using password grant is now deprecated, 
    // but kept for compatibility until components are updated.
    return await authLogin(email, password);
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
    authLogin,
    handleCallback,
    login,
    logout,
  };
});
