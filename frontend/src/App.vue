<script setup lang="ts">
import { watch } from 'vue'
import Menu from '@/views/Menu.vue'
import { useRuntimeStore, useUserStore } from '@/stores'
import { client } from '@/api/client.gen'

const userStore = useUserStore()
const runtimeStore = useRuntimeStore()

client.instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      userStore.logout()
    }
    return Promise.reject(error)
  },
)

watch(
  () => userStore.isAuthenticated,
  (isAuthenticated) => {
    if (isAuthenticated) {
      void runtimeStore.initializeRealtime()
    } else {
      runtimeStore.teardownRealtime()
    }
  },
  { immediate: true },
)
</script>

<template>
  <v-app>
    <Menu />

    <v-main>
      <v-container>
        <router-view />
      </v-container>
    </v-main>

    <v-footer app>
      <span>&copy; {{ new Date().getFullYear() }} - Routine Cloud</span>
    </v-footer>
  </v-app>
</template>
