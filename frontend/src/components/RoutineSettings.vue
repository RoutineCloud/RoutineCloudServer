<script setup lang="ts">
import {computed} from 'vue'
import {RoutineRead, StartMode} from '@/api'
import {useRoutinesStore} from '@/stores/routines'

const props = defineProps<{
  routine: RoutineRead
}>()

const routinesStore = useRoutinesStore()

const startMode = computed({
  get: () => props.routine.start_mode as StartMode,
  set: async (val: StartMode) => {
    await routinesStore.update(props.routine.id, { start_mode: val })
  }
})

const notifyOptions = [
  { label: 'Notify on Start', value: 1 },
  { label: 'Notify on Finish', value: 2 },
  { label: 'Notify on Progress', value: 4 },
  { label: 'Notify on Pause', value: 8 },
  { label: 'Notify on Skip', value: 16 },
]

function isNotifySet(bit: number) {
  return (props.routine.notify_mask & bit) !== 0
}

async function toggleNotify(bit: number) {
  const newMask = isNotifySet(bit) 
    ? props.routine.notify_mask & ~bit 
    : props.routine.notify_mask | bit
  await routinesStore.update(props.routine.id, { notify_mask: newMask })
}
</script>

<template>
  <v-card class="mt-4">
    <v-card-title class="text-h6">Personal Settings</v-card-title>
    <v-divider></v-divider>
    <v-card-text>
      <div class="mb-4">
        <label class="text-subtitle-2 d-block mb-1">Start Mode</label>
        <v-select
          v-model="startMode"
          :items="[
            { title: 'Manual Only', value: 'none' },
            { title: 'Follow Owner', value: 'follow_owner' },
            { title: 'Follow Any', value: 'follow_any' }
          ]"
          density="compact"
          variant="outlined"
          hide-details
        />
        <div class="text-caption text-medium-emphasis mt-1">
          Decide if this routine starts automatically when others start it.
        </div>
      </div>
      
      <div class="text-subtitle-2 mt-4 mb-1">Notifications</div>
      <v-row dense>
        <v-col v-for="opt in notifyOptions" :key="opt.value" cols="12" sm="6">
          <v-checkbox
            :label="opt.label"
            :model-value="isNotifySet(opt.value)"
            @update:model-value="toggleNotify(opt.value)"
            density="compact"
            hide-details
            color="primary"
          />
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>
