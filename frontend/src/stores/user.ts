import {defineStore} from 'pinia';
import {computed, ref, watch} from 'vue';
import {Users} from "@/api";
import {userManager} from '@/auth';
import type {User as OidcUser} from 'oidc-client-ts';

type User = {
    username: string;
    email: string;
    id: number;
    is_superuser: boolean;
}

export const useUserStore = defineStore('user', () => {
  // State
  const oidcUser = ref<OidcUser | null>(null);
  const user = ref<User | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Initialize
  userManager.getUser().then(u => {
    oidcUser.value = u;
  });

  // Events
  userManager.events.addUserLoaded((u) => {
    oidcUser.value = u;
  });
  userManager.events.addUserUnloaded(() => {
    oidcUser.value = null;
  });

  if (localStorage.getItem("user") && localStorage.getItem("user") !== null && localStorage.getItem("user") !== "undefined") {
    user.value = JSON.parse(localStorage.getItem("user") as string)
  }

  // Watch for OIDC user changes
  watch(
    () => oidcUser.value,
    (u) => {
      if (u && !user.value) {
        fetchUserProfile();
      } else if (!u) {
        user.value = null;
        localStorage.removeItem("user");
      }
    },
    { immediate: true }
  );

  // Getters
  const isAuthenticated = computed(() => !!user.value || !!oidcUser.value);
  const userProfile = computed(() => user.value);
  const accessToken = computed(() => oidcUser.value?.access_token);

  // Actions
  async function fetchUserProfile() {
    loading.value = true;
    error.value = null;
    try {
      const {data: userData} = await Users.usersMe();
      user.value = userData as any;
      localStorage.setItem("user", JSON.stringify(userData));
      return true;
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
      error.value = 'Failed to fetch user profile';
      return false;
    } finally {
      loading.value = false;
    }
  }

  function login() {
    userManager.signinRedirect();
  }

  async function logout() {
    try {
      await userManager.signoutRedirect();
    } catch (err) {
      console.error('Logout failed:', err);
      // Fallback cleanup
      oidcUser.value = null;
      user.value = null;
      localStorage.removeItem("user");
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
    accessToken,

    // Actions
    fetchUserProfile,
    login,
    logout,
  };
});
