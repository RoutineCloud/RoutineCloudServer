<script setup lang="ts">
import {onMounted} from 'vue'
import {useDeviceStore, useUserStore} from '@/stores/index.js'

const devicesStore = useDeviceStore()
const userStore = useUserStore()

onMounted(async () => {
  await devicesStore.load()
})

function refresh() {
  devicesStore.load()
}

function statusColor(status?: string) {
  if (status === 'online') return 'green'
  if (status === 'offline') return 'grey'
  return 'grey'
}
</script>

<template>
  <div class="profile-page">
    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title class="text-h6">Profile</v-card-title>
          <v-card-text>
            <div class="mb-2"><strong>Username:</strong> {{ userStore.user?.username }}</div>
            <div class="mb-2"><strong>Email:</strong> {{ userStore.user?.email }}</div>
            <div class="mb-2"><strong>User ID:</strong> {{ userStore.user?.id }}</div>
            <div class="mb-2"><strong>Admin:</strong> {{ userStore.user?.is_superuser ? 'Yes' : 'No' }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center" style="gap: 8px">
            <span class="text-h6">Devices</span>
            <v-spacer></v-spacer>
            <v-btn :loading="devicesStore.loading" @click="refresh" variant="text" icon="mdi-refresh" :title="'Refresh'" />
          </v-card-title>
          <v-card-text>
            <div v-if="devicesStore.error">
              <v-alert type="error" density="comfortable">{{ devicesStore.error }}</v-alert>
            </div>
            <div v-else>
              <v-skeleton-loader v-if="devicesStore.loading" type="list-item-two-line@3" />
              <template v-else>
                <v-list v-if="devicesStore.devices.length > 0" density="comfortable">
                  <v-list-item v-for="d in devicesStore.devices" :key="d.id">
                    <template #prepend>
                      <v-avatar color="primary" size="28">
                        <v-icon size="18">mdi-chip</v-icon>
                      </v-avatar>
                    </template>
                    <v-list-item-title>{{ d.name }}</v-list-item-title>
                    <v-list-item-subtitle>Type: {{ d.type }}</v-list-item-subtitle>
                    <template #append>
                      <v-chip :color="statusColor(d.status as any)" label size="small" class="mr-2" variant="flat">
                        {{ d.status }}
                      </v-chip>
                      <v-chip :color="d.is_active ? 'blue' : 'grey'" label size="small" variant="outlined">
                        {{ d.is_active ? 'Active' : 'Inactive' }}
                      </v-chip>
                    </template>
                  </v-list-item>
                </v-list>
                <v-alert v-else type="info" variant="tonal" title="No devices">
                  You have no devices yet.
                </v-alert>
              </template>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>

</template>

<style scoped>
.profile-page {
  padding-top: 8px;
}
</style>