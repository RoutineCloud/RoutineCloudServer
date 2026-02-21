<script setup lang="ts">
import {ref} from 'vue'
import ChangePassword from '@/components/ChangePassword.vue'
import DevicesPanel from '@/components/DevicesPanel.vue'
import {useUserStore} from '@/stores/index.js'

const userStore = useUserStore()
const activeTab = ref('profile')

const menuItems = [
  { id: 'profile', title: 'Profile', icon: 'mdi-account' },
  { id: 'devices', title: 'Devices', icon: 'mdi-chip' },
  { id: 'password', title: 'Change Password', icon: 'mdi-lock-reset' }
]
</script>

<template>
  <v-container class="konto-page">
    <v-row>
      <v-col cols="12" md="3">
        <v-card variant="flat" border class="mb-4">
          <v-list density="comfortable">
            <v-list-item
              v-for="item in menuItems"
              :key="item.id"
              :active="activeTab === item.id"
              @click="activeTab = item.id"
              color="primary"
              link
            >
              <template v-slot:prepend>
                <v-icon :icon="item.icon" size="small"></v-icon>
              </template>
              <v-list-item-title>{{ item.title }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="9">
        <v-card variant="flat" border class="pa-6">
          <div v-if="activeTab === 'profile'">
            <div class="text-h6 mb-4">User Profile</div>
            <div class="mb-4">
              <div class="text-caption text-grey">Username</div>
              <div class="text-body-1">{{ userStore.user?.username }}</div>
            </div>
            <div class="mb-4">
              <div class="text-caption text-grey">Email</div>
              <div class="text-body-1">{{ userStore.user?.email }}</div>
            </div>
            <div class="mb-4">
              <div class="text-caption text-grey">User ID</div>
              <div class="text-body-1">{{ userStore.user?.id }}</div>
            </div>
            <div class="mb-4">
              <div class="text-caption text-grey">Admin Status</div>
              <div class="text-body-1">{{ userStore.user?.is_superuser ? 'Administrator' : 'Regular User' }}</div>
            </div>
          </div>

          <div v-if="activeTab === 'devices'">
            <DevicesPanel />
          </div>

          <div v-if="activeTab === 'password'">
            <ChangePassword />
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.konto-page {
  padding-top: 16px;
}
</style>
