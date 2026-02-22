<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {useUserStore} from '@/stores/user'
import UsersPanel from '@/components/admin/UsersPanel.vue'
import OAuthClientsPanel from '@/components/admin/OAuthClientsPanel.vue'

const tabs = [
  { key: 'users', title: 'Users', icon: 'mdi-account-multiple' },
  { key: 'oauth', title: 'OAuth Clients', icon: 'mdi-shield-key' },
]

const active = ref('users')
const userStore = useUserStore()
const router = useRouter()

onMounted(() => {
  if (!userStore.user?.is_superuser) {
    router.replace('/')
  }
})
</script>

<template>
  <div class="admin-page">
    <v-row>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title class="text-h6">Admin</v-card-title>
          <v-divider />
          <v-list density="comfortable">
            <v-list-item
              v-for="t in tabs"
              :key="t.key"
              :value="t.key"
              :active="active === t.key"
              @click="active = t.key"
            >
              <template #prepend>
                <v-icon size="18">{{ t.icon }}</v-icon>
              </template>
              <v-list-item-title>{{ t.title }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="9">
        <UsersPanel v-if="active === 'users'" />
        <OAuthClientsPanel v-if="active === 'oauth'" />
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.admin-page {
  padding-top: 8px;
}
</style>
