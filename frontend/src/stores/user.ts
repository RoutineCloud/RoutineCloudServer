import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import VueJwtDecode from 'vue-jwt-decode';
import {Oauth2, Users} from "@/api";

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
        const {data, error} = await Oauth2.oauthToken({
            body: {
                grant_type: "password",
                client_id: "routine-web",
                username: email,
                password: password
            }
        })

        if (error) {
            console.error('Login failed:', error);
            error.value = 'Invalid email or password';
            return false;
        }

         const { access_token,
          token_type,
          refresh_token,
          expires_in
        } = data;

        localStorage.setItem('auth_token', access_token);


        // Decode JWT token to get user ID
        const decoded = VueJwtDecode.decode(access_token)
        console.log("Decoded token:", decoded)
        
        let responseUser = {
            id: decoded.sub,
        }
        user.value = responseUser;

        localStorage.setItem("user", JSON.stringify(responseUser));

        // Fetch user profile info
        const {data: userData, error: userError} = await Users.usersMe();
        if (userError) {
            console.error('Failed to fetch user profile:', userError);
            error.value = 'Failed to fetch user profile';
            return false;
        }
        responseUser = {
            id: decoded.sub,
            ...userData
        }
        user.value = responseUser;
        localStorage.setItem("user", JSON.stringify(responseUser));

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
