<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref} from 'vue'
import {useRoutinesStore} from '@/stores/routines'
import {formatSecondsToTime, parseUtcDate} from '@/utils/time'

const routinesStore = useRoutinesStore()
const actionLoading = ref(false)
const tickNow = ref(Date.now())
let tickTimer: number | null = null

const activeName = computed(() => routinesStore.activeStatus?.routine_name)
const hasActiveRoutine = computed(() => routinesStore.hasActiveRoutine)
const isPaused = computed(() => routinesStore.isActivePaused)
const activeRoutineId = computed(() => routinesStore.activeStatus?.active_routine_id ?? null)
const currentTaskPosition = computed(() => routinesStore.activeStatus?.current_task_position ?? null)
const currentTaskStartedAt = computed(() => routinesStore.activeStatus?.started_at ?? null)
const pausedAt = computed(() => routinesStore.activeStatus?.paused_at ?? null)

const activeRoutine = computed(() => {
  if (!activeRoutineId.value) return null
  return routinesStore.all.find(r => r.id === activeRoutineId.value) ?? null
})

const sortedRoutineTasks = computed(() => {
  const tasks = activeRoutine.value?.tasks ?? []
  return [...tasks].sort((a, b) => a.position - b.position)
})

const currentTask = computed(() => {
  if (!currentTaskPosition.value) return null
  return sortedRoutineTasks.value.find(t => t.position === currentTaskPosition.value) ?? null
})

const currentTaskElapsedSeconds = computed(() => {
  const startedAt = currentTaskStartedAt.value
  if (!startedAt) return 0

  const startedAtMs = parseUtcDate(startedAt)
  if (Number.isNaN(startedAtMs)) return 0

  if (isPaused.value && pausedAt.value) {
    const pausedAtMs = parseUtcDate(pausedAt.value)
    if (!Number.isNaN(pausedAtMs)) {
      return Math.max(Math.floor((pausedAtMs - startedAtMs) / 1000), 0)
    }
  }

  return Math.max(Math.floor((tickNow.value - startedAtMs) / 1000), 0)
})

const currentTaskRemainingSeconds = computed(() => {
  const duration = currentTask.value?.duration ?? 0
  return Math.max(duration - currentTaskElapsedSeconds.value, 0)
})

const routineRemainingSeconds = computed(() => {
  if (!activeRoutine.value) return 0
  const allTasks = sortedRoutineTasks.value
  const totalRoutineSeconds = allTasks.reduce((sum, task) => sum + (task.duration ?? 0), 0)
  const currentPos = currentTaskPosition.value

  if (!currentPos) return totalRoutineSeconds

  const elapsedBeforeCurrent = allTasks
    .filter(task => task.position < currentPos)
    .reduce((sum, task) => sum + (task.duration ?? 0), 0)

  const currentDuration = currentTask.value?.duration ?? 0
  const elapsedCurrent = Math.min(currentTaskElapsedSeconds.value, currentDuration)
  return Math.max(totalRoutineSeconds - (elapsedBeforeCurrent + elapsedCurrent), 0)
})

const formattedTaskRemaining = computed(() => formatSecondsToTime(currentTaskRemainingSeconds.value))
const formattedRoutineRemaining = computed(() => formatSecondsToTime(routineRemainingSeconds.value))

onMounted(async () => {
  if (routinesStore.all.length === 0) {
    await routinesStore.load()
  }
  await routinesStore.loadActiveStatus()
  tickTimer = window.setInterval(() => {
    tickNow.value = Date.now()
    if (hasActiveRoutine.value && !isPaused.value) {
      if (currentTaskRemainingSeconds.value <= 0) {
        advanceTaskLocally()
      }
    }
  }, 1000)
})

function advanceTaskLocally() {
  if (!routinesStore.activeStatus || !activeRoutine.value) return

  const tasks = sortedRoutineTasks.value
  const currentPos = currentTaskPosition.value ?? 0
  const nextTask = tasks.find(t => t.position > currentPos)

  if (nextTask) {
    routinesStore.activeStatus.current_task_position = nextTask.position
    routinesStore.activeStatus.started_at = new Date().toISOString()
  } else {
    routinesStore.activeStatus = null
  }
}

async function togglePlayPause() {
  if (!hasActiveRoutine.value || actionLoading.value) return
  actionLoading.value = true
  try {
    if (isPaused.value) {
      await routinesStore.resumeActive()
    } else {
      await routinesStore.pauseActive()
    }
  } catch (e) {
    console.error('Failed to toggle active routine state', e)
  } finally {
    actionLoading.value = false
  }
}


async function stopRoutine() {
  if (!hasActiveRoutine.value || actionLoading.value) return
  actionLoading.value = true
  try {
    await routinesStore.stopActive()
  } catch (e) {
    console.error('Failed to stop active routine', e)
  } finally {
    actionLoading.value = false
  }
}

onBeforeUnmount(() => {
  if (tickTimer !== null) {
    window.clearInterval(tickTimer)
    tickTimer = null
  }
})
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
        <v-spacer></v-spacer>
        <v-btn
          :icon="isPaused ? 'mdi-play' : 'mdi-pause'"
          size="small"
          variant="text"
          :loading="actionLoading"
          :disabled="actionLoading"
          @click="togglePlayPause"
        />
        <v-btn
          icon="mdi-stop"
          size="small"
          variant="text"
          color="error"
          :loading="actionLoading"
          :disabled="actionLoading"
          @click="stopRoutine"
        />
      </template>
      <template v-else>
        <div class="text-medium-emphasis">Keine Routine gestartet</div>
      </template>
    </v-card-text>
  </v-card>
</template>
