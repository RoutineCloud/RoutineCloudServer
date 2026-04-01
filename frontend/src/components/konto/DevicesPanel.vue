<script setup lang="ts">
import {onMounted} from 'vue'
import {useDeviceStore} from '@/stores/index.js'
import {DeviceStatus} from '@/api'

const devicesStore = useDeviceStore()

onMounted(async () => {
  await devicesStore.load()
})

function refresh() {
  devicesStore.load()
}

function statusColor(status?: DeviceStatus) {
  if (status === DeviceStatus.ONLINE) return 'green'
  if (status === DeviceStatus.OFFLINE) return 'grey'
  return 'grey'
}
</script>

<template>
  <div class="devices-panel">
    <div class="d-flex align-center mb-4" style="gap: 8px">
      <span class="text-h6">Devices</span>
      <v-spacer></v-spacer>
      <v-btn :loading="devicesStore.loading" @click="refresh" variant="text" icon="mdi-refresh" :title="'Refresh'" />
    </div>

    <div v-if="devicesStore.error">
      <v-alert type="error" density="comfortable">{{ devicesStore.error }}</v-alert>
    </div>
    <div v-else>
      <v-skeleton-loader v-if="devicesStore.loading" type="list-item-two-line@3" />
      <template v-else>
        <v-list v-if="devicesStore.devices.length > 0" density="comfortable" class="bg-transparent pa-0">
          <v-list-item v-for="d in devicesStore.devices" :key="d.id" class="px-0">
            <template #prepend>
              <v-avatar color="primary" size="32" class="mr-3">
                <v-icon size="20">mdi-chip</v-icon>
              </v-avatar>
            </template>
            <v-list-item-title class="font-weight-medium">{{ d.name }}</v-list-item-title>
            <v-list-item-subtitle>Type: {{ d.type || 'N/A' }}</v-list-item-subtitle>
            <template #append>
              <v-chip :color="statusColor(d.status)" label size="small" class="mr-2" variant="flat">
                {{ d.status }}
              </v-chip>
              <v-chip :color="d.is_active ? 'blue' : 'grey'" label size="small" variant="outlined">
                {{ d.is_active ? 'Active' : 'Inactive' }}
              </v-chip>
            </template>
          </v-list-item>
        </v-list>
        <v-alert v-else type="info" variant="tonal">
          You have no devices yet. Use the "Link Device" page to connect one.
        </v-alert>
      </template>
    </div>
  </div>
</template>

<style scoped>
.devices-panel {
  min-height: 200px;
}
</style>
