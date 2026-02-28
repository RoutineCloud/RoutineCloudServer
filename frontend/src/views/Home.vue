<script setup lang="ts">
import {useUserStore} from '@/stores/index.js'

const userStore = useUserStore()

const login = () => {
  userStore.login()
}
</script>

<template>
  <div class="home">
    <!-- Hero / Landing Section -->
    <v-sheet class="py-12 px-4 px-md-8" color="transparent">
      <v-container class="text-center">
        <div class="text-h3 text-md-h2 font-weight-bold mb-3">Routine Cloud</div>
        <div class="text-subtitle-1 text-medium-emphasis mb-6">
          Plan, start, and track your daily routines — synced across your devices in real time.
        </div>
        <div class="d-flex align-center justify-center" style="gap: 12px">
          <v-btn
            v-if="!userStore.isAuthenticated"
            color="primary"
            size="large"
            class="px-6"
            @click="login"
          >Get Started</v-btn>
          <v-btn
            v-else
            color="primary"
            size="large"
            class="px-6"
            to="/routines"
          >Go to Routines</v-btn>
          <v-btn variant="text" size="large" to="/about">Learn more</v-btn>
        </div>
      </v-container>
    </v-sheet>

    <!-- Feature Highlights -->
    <v-container class="my-6">
      <v-row>
        <v-col cols="12" md="4">
          <v-card class="h-100" variant="outlined">
            <v-card-item>
              <template #prepend>
                <v-avatar color="primary" size="40"><v-icon>mdi-playlist-check</v-icon></v-avatar>
              </template>
              <v-card-title>Create powerful routines</v-card-title>
              <v-card-subtitle>Build task sequences with durations</v-card-subtitle>
            </v-card-item>
            <v-card-text>
              Combine tasks into routines, reorder, duplicate, and fine‑tune timing. Keep your day on track.
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card class="h-100" variant="outlined">
            <v-card-item>
              <template #prepend>
                <v-avatar color="primary" size="40"><v-icon>mdi-websocket</v-icon></v-avatar>
              </template>
              <v-card-title>Real‑time control</v-card-title>
              <v-card-subtitle>WebSocket powered updates</v-card-subtitle>
            </v-card-item>
            <v-card-text>
              Start a routine and all connected devices react instantly — no refresh required.
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card class="h-100" variant="outlined">
            <v-card-item>
              <template #prepend>
                <v-avatar color="primary" size="40"><v-icon>mdi-devices</v-icon></v-avatar>
              </template>
              <v-card-title>Your devices</v-card-title>
              <v-card-subtitle>Link and monitor device status</v-card-subtitle>
            </v-card-item>
            <v-card-text>
              Connect your devices and see online/offline status right in your profile.
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>