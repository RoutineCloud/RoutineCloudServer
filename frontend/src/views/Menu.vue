<script setup lang="ts">
import {ref} from 'vue'
import {useUserStore} from '@/stores/user.ts'

const userStore = useUserStore()
const menu = ref(false)

const logout = () => {
  userStore.logout()
}
</script>

<template>
  <v-app-bar app color="primary" dark>
      <v-app-bar-title>Routine Cloud</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn to="/" text>Home</v-btn>
      <v-btn to="/about" text>About</v-btn>
      <v-btn v-if="userStore.isAuthenticated" to="/routines" text>Routines</v-btn>
      <v-btn v-if="userStore.isAuthenticated" to="/tasks" text>Tasks</v-btn>

      <v-btn v-if="!userStore.isAuthenticated" to="/login" text>Login</v-btn>
      <div v-if="userStore.isAuthenticated">
        <v-menu v-model="menu" :close-on-content-click="false">
          <template v-slot:activator="{ props }">
            <v-btn icon v-bind="props">
              <v-icon>mdi-account-circle</v-icon>
            </v-btn>
          </template>
          <v-card min-width="200">
            <v-list>
              <v-list-item>
                <v-list-item-title>{{ userStore.user.username }}</v-list-item-title>
              </v-list-item>
              <v-list-item to="/profile">Profile</v-list-item>
              <v-list-item to="/konto">Konto</v-list-item>
              <v-divider></v-divider>
              <v-list-item @click="logout">
                <v-list-item-title>Logout</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card>
        </v-menu>
      </div>

    </v-app-bar>
</template>

<style scoped>

</style>