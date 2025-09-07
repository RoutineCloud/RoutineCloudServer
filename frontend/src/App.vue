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
export default {
  name: 'App',
  components: {Menu},
  data: () => ({
    //
  }),
}
</script>