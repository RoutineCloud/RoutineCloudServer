<script setup lang="ts">
import {ref} from 'vue'
import ChangePassword from '@/components/ChangePassword.vue'
import ProfilePanel from '@/components/konto/ProfilePanel.vue'
import FriendsPanel from '@/components/konto/FriendsPanel.vue'
import DevicesPanel from '@/components/konto/DevicesPanel.vue'

const activeTab = ref('profile')

const menuItems = [
  { id: 'profile', title: 'Profile', icon: 'mdi-account' },
  { id: 'friends', title: 'Friends', icon: 'mdi-account-group' },
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
            <ProfilePanel />
          </div>

          <div v-if="activeTab === 'friends'">
            <FriendsPanel />
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
