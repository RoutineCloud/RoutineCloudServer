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


<script>
import Menu from '@/views/Menu.vue'
import {useUserStore} from "@/stores/index.js";
import {client} from "@/api/client.gen.js";


// Global 401 handler -> logout
client.instance.interceptors.response.use(
  r => {
    return r
  },
  err => {
    if (err.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
    }
    return Promise.reject(err)
  }
)

export default {
  name: 'App',
  components: {Menu},
  data: () => ({
    //
  }),
}
</script>
