<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import {useRoutinesStore} from '@/stores/routines'
import {useRuntimeStore} from '@/stores/runtime'
import {formatSecondsToTime} from '@/utils/time'

const routinesStore = useRoutinesStore()
const runtimeStore = useRuntimeStore()
const {
  activeRoutine,
  currentTask,
  canControl,
  hasActiveRoutine,
  isPaused,
  runtimeState,
  routineRemainingSeconds,
  taskRemainingSeconds,
} = storeToRefs(runtimeStore)

const actionLoading = ref(false)

const activeName = computed(() => activeRoutine.value?.name ?? null)

const formattedTaskRemaining = computed(() =>
  formatSecondsToTime(taskRemainingSeconds.value),
)
const formattedRoutineRemaining = computed(() =>
  formatSecondsToTime(routineRemainingSeconds.value),
)

onMounted(async () => {
  if (routinesStore.all.length === 0) {
    await routinesStore.load()
  }
})

async function togglePlayPause() {
  if (!hasActiveRoutine.value || actionLoading.value || !canControl.value) return
  actionLoading.value = true
  try {
    if (isPaused.value) {
      await runtimeStore.resumeRoutine()
    } else {
      await runtimeStore.pauseRoutine()
    }
  } catch (error) {
    console.error('Failed to toggle active routine state', error)
  } finally {
    actionLoading.value = false
  }
}

async function stopRoutine() {
  if (!hasActiveRoutine.value || actionLoading.value || !canControl.value) return
  actionLoading.value = true
  try {
    await runtimeStore.stopRoutine()
  } catch (error) {
    console.error('Failed to stop active routine', error)
  } finally {
    actionLoading.value = false
  }
}

async function skipTask() {
  if (!hasActiveRoutine.value || actionLoading.value || !canControl.value) return
  actionLoading.value = true
  try {
    await runtimeStore.skipRoutine()
  } catch (error) {
    console.error('Failed to skip active task', error)
  } finally {
    actionLoading.value = false
  }
}
</script>

<template>
  <v-card variant="tonal" class="mb-4">
    <v-card-text class="d-flex align-center flex-wrap" style="gap: 12px">
      <template v-if="hasActiveRoutine">
        <div class="font-weight-medium">{{ activeName }}</div>
        <div class="text-medium-emphasis">|</div>
        <div class="d-flex align-center" style="gap: 6px">
          <font-awesome-icon
            :icon="['fas', currentTask?.icon_name || 'list-check']"
            class="text-medium-emphasis"
          />
          <span>Aktueller Task: <span class="font-weight-medium">{{ currentTask?.name ?? '-' }}</span></span>
        </div>
        <div class="text-medium-emphasis">|</div>
        <div>Rest Task: <span class="font-weight-medium">{{ formattedTaskRemaining }}</span></div>
        <div class="text-medium-emphasis">|</div>
        <div>Rest Routine: <span class="font-weight-medium">{{ formattedRoutineRemaining }}</span></div>
        <v-spacer />
        <v-btn
          icon="mdi-skip-next"
          size="small"
          variant="text"
          :loading="actionLoading"
          :disabled="actionLoading || !canControl"
          @click="skipTask"
        />
        <v-btn
          :icon="isPaused ? 'mdi-play' : 'mdi-pause'"
          size="small"
          variant="text"
          :loading="actionLoading"
          :disabled="actionLoading || !canControl"
          @click="togglePlayPause"
        />
        <v-btn
          icon="mdi-stop"
          size="small"
          variant="text"
          color="error"
          :loading="actionLoading"
          :disabled="actionLoading || !canControl"
          @click="stopRoutine"
        />
      </template>
      <template v-else>
        <div class="text-medium-emphasis">Keine Routine gestartet</div>
      </template>
    </v-card-text>
  </v-card>
</template>
