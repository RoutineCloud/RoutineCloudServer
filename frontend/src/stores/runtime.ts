import {computed, ref, watch} from 'vue'
import {
  Runtime,
  type RuntimeActiveRead,
  type RuntimeCommandAccepted,
  type RuntimeCommandRequest,
  type RuntimeCommandType,
  type RuntimeEventEnvelope,
  type RuntimeSyncRead,
  type TaskInRoutineRead,
} from '@/api'
import {defineStore} from 'pinia'
import {useRoutinesStore} from '@/stores/routines'
import {parseUtcDate} from '@/utils/time'

function createCommandId(type: RuntimeCommandType): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${type}-${crypto.randomUUID()}`
  }
  return `${type}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export const useRuntimeStore = defineStore('runtime', () => {
  const routinesStore = useRoutinesStore()
  const activeRuntime = ref<RuntimeActiveRead | null>(null)
  const timeOffsetMs = ref(0)
  const connecting = ref(false)
  const tickNowMs = ref(Date.now())

  let eventsAbortController: AbortController | null = null
  let visibilityHandler: (() => void) | null = null
  let streamPromise: Promise<void> | null = null
  let tickTimer: number | null = null
  let routinesLoadPromise: Promise<void> | null = null

  const runtimeState = computed(() => activeRuntime.value?.runtime ?? null)
  const activeRoutine = computed(() => activeRuntime.value?.routine ?? null)
  const hasActiveRoutine = computed(() => !!runtimeState.value?.routine_id)
  const isPaused = computed(() => runtimeState.value?.status === 'paused')
  const isRunning = computed(() => runtimeState.value?.status === 'running')
  const sortedRoutineTasks = computed(() =>
    [...(activeRoutine.value?.tasks ?? [])].sort((a, b) => a.position - b.position),
  )
  const canControl = computed(() => {
    const routineId = runtimeState.value?.routine_id
    if (!routineId) return false
    const routine = routinesStore.all.find((entry) => entry.id === routineId)
    return routine?.access_level === 'owner' || routine?.access_level === 'start'
  })
  const derivedProgress = computed(() => {
    const runtime = runtimeState.value
    const tasks = sortedRoutineTasks.value
    if (!runtime?.routine_id || !runtime.task_started_at || tasks.length === 0) {
      return {
        currentTask: null as TaskInRoutineRead | null,
        currentTaskElapsedSeconds: 0,
        currentTaskRemainingSeconds: 0,
        routineRemainingSeconds: 0,
        isFinished: false,
      }
    }

    const currentTask = tasks.find((t) => t.position === runtime.current_task_position)
    if (!currentTask) {
      return {
        currentTask: null as TaskInRoutineRead | null,
        currentTaskElapsedSeconds: 0,
        currentTaskRemainingSeconds: 0,
        routineRemainingSeconds: 0,
        isFinished: true,
      }
    }

    const taskStartedAtMs = parseUtcDate(runtime.task_started_at)
    const referenceMs =
      runtime.status === 'paused' && runtime.paused_at
        ? parseUtcDate(runtime.paused_at)
        : tickNowMs.value + timeOffsetMs.value
    const safeReferenceMs = Number.isNaN(referenceMs) ? tickNowMs.value + timeOffsetMs.value : referenceMs
    const taskElapsed = Math.max(0, Math.floor((safeReferenceMs - taskStartedAtMs) / 1000))
    const duration = Math.max(currentTask.duration ?? 0, 0)

    const currentIndex = tasks.indexOf(currentTask)
    const remainingTasksDuration = tasks.slice(currentIndex + 1).reduce((sum, t) => sum + (t.duration ?? 0), 0)
    const currentTaskRemaining = Math.max(0, duration - taskElapsed)

    return {
      currentTask,
      currentTaskElapsedSeconds: taskElapsed,
      currentTaskRemainingSeconds: currentTaskRemaining,
      routineRemainingSeconds: currentTaskRemaining + remainingTasksDuration,
      isFinished: taskElapsed >= duration,
    }
  })
  const currentTask = computed(() => derivedProgress.value.currentTask)
  const taskRemainingSeconds = computed(() => derivedProgress.value.currentTaskRemainingSeconds)
  const routineRemainingSeconds = computed(() => derivedProgress.value.routineRemainingSeconds)

  function updateTimeOffset(serverTime: string) {
    const parsed = parseUtcDate(serverTime)
    if (!Number.isNaN(parsed)) {
      const currentOffset = parsed - Date.now()
      // Use a moving average to smooth the offset and reduce jitter from network latency
      if (timeOffsetMs.value === 0) {
        timeOffsetMs.value = currentOffset
      } else {
        // Weighted average: 80% old, 20% new
        timeOffsetMs.value = Math.round(timeOffsetMs.value * 0.8 + currentOffset * 0.2)
      }
    }
  }

  function applyActive(payload: RuntimeActiveRead) {
    activeRuntime.value = payload
    updateTimeOffset(payload.server_time)
  }

  function applySync(payload: RuntimeSyncRead) {
    updateTimeOffset(payload.server_time)
    if (!activeRuntime.value) {
      activeRuntime.value = {
        server_time: payload.server_time,
        runtime: payload.runtime,
      }
      return
    }

    const currentRoutine =
      activeRuntime.value.runtime.routine_id === payload.runtime.routine_id
        ? activeRuntime.value.routine
        : undefined

    activeRuntime.value = {
      server_time: payload.server_time,
      runtime: payload.runtime,
      routine: currentRoutine,
    }
  }

  async function loadActive() {
    const { data } = await Runtime.runtimeActive()
    applyActive(data)
    return data
  }

  async function loadSync() {
    const { data } = await Runtime.runtimeSync()
    const routineChanged =
      activeRuntime.value?.runtime.routine_id !== data.runtime.routine_id

    if (routineChanged && data.runtime.routine_id) {
      await loadActive()
      return activeRuntime.value
    }

    applySync(data)
    return data
  }

  function applyCommandResult(result: RuntimeCommandAccepted) {
    if (result.active) {
      applyActive(result.active)
      return
    }
    applySync(result.sync)
  }

  async function sendCommand(type: RuntimeCommandType, routineId?: number) {
    const body: RuntimeCommandRequest = {
      command_id: createCommandId(type),
      type,
      routine_id: routineId,
      requested_at: new Date().toISOString(),
    }

    let response
    switch (type) {
      case 'routine.start':
        response = await Runtime.runtimeStart({ body })
        break
      case 'routine.pause':
        response = await Runtime.runtimePause({ body })
        break
      case 'routine.resume':
        response = await Runtime.runtimeResume({ body })
        break
      case 'routine.skip':
        response = await Runtime.runtimeSkip({ body })
        break
      case 'routine.stop':
        response = await Runtime.runtimeStop({ body })
        break
      case 'routine.complete':
        response = await Runtime.runtimeComplete({ body })
        break
      default:
        throw new Error(`Unsupported runtime command: ${type}`)
    }

    applyCommandResult(response.data)
    return response.data
  }

  async function startRoutine(routineId: number) {
    const routine = routinesStore.all.find((r) => r.id === routineId)
    if (routine && routine.access_level === 'read') {
      throw new Error('Insufficient permissions to start this routine')
    }
    return sendCommand('routine.start', routineId)
  }

  async function pauseRoutine() {
    if (!canControl.value) return
    return sendCommand('routine.pause')
  }

  async function resumeRoutine() {
    if (!canControl.value) return
    return sendCommand('routine.resume')
  }

  async function skipRoutine() {
    if (!canControl.value) return
    return sendCommand('routine.skip')
  }

  async function stopRoutine() {
    if (!canControl.value) return
    return sendCommand('routine.stop')
  }

  async function completeRoutine() {
    if (!canControl.value) return
    return sendCommand('routine.complete')
  }

  function handleRuntimeEvent(event: RuntimeEventEnvelope) {
    if (event.active) {
      applyActive(event.active)
    } else if (event.sync) {
      applySync(event.sync)
    }
  }

  async function connectEvents() {
    if (connecting.value || streamPromise) {
      return
    }

    connecting.value = true
    eventsAbortController = new AbortController()
    streamPromise = (async () => {
      try {
        const result = await Runtime.runtimeEvents({
          signal: eventsAbortController?.signal,
          onSseError: async () => {
            if (!eventsAbortController?.signal.aborted) {
              await loadSync().catch(() => undefined)
            }
          },
        })

        for await (const payload of result.stream as AsyncGenerator<RuntimeEventEnvelope>) {
          handleRuntimeEvent(payload)
        }
      } finally {
        connecting.value = false
        streamPromise = null
      }
    })()
  }

  function disconnectEvents() {
    eventsAbortController?.abort()
    eventsAbortController = null
    connecting.value = false
    streamPromise = null
  }

  function startTicker() {
    if (tickTimer !== null) {
      return
    }

    tickTimer = window.setInterval(() => {
      tickNowMs.value = Date.now()
    }, 1000)
  }

  function stopTicker() {
    if (tickTimer !== null) {
      window.clearInterval(tickTimer)
      tickTimer = null
    }
    tickNowMs.value = Date.now()
  }

  async function ensureRoutineAccessLoaded() {
    const routineId = runtimeState.value?.routine_id
    if (!routineId) {
      return
    }
    if (routinesStore.all.some((routine) => routine.id === routineId)) {
      return
    }
    if (routinesLoadPromise) {
      return routinesLoadPromise
    }

    routinesLoadPromise = routinesStore
      .load()
      .catch(() => undefined)
      .finally(() => {
        routinesLoadPromise = null
      })

    return routinesLoadPromise
  }


  async function initializeRealtime() {
    await loadActive().catch(() => undefined)
    await ensureRoutineAccessLoaded()
    await connectEvents()
    startTicker()

    if (!visibilityHandler) {
      visibilityHandler = () => {
        if (document.visibilityState === 'visible') {
          void loadSync().catch(() => undefined)
        }
      }
      document.addEventListener('visibilitychange', visibilityHandler)
    }
  }

  function teardownRealtime() {
    disconnectEvents()
    stopTicker()
    if (visibilityHandler) {
      document.removeEventListener('visibilitychange', visibilityHandler)
      visibilityHandler = null
    }
    activeRuntime.value = null
    timeOffsetMs.value = 0
  }

  watch(
    () => runtimeState.value?.routine_id,
    () => {
      tickNowMs.value = Date.now()
      void ensureRoutineAccessLoaded()
    },
    { immediate: true },
  )

  return {
    activeRuntime,
    activeRoutine,
    currentTask,
    canControl,
    hasActiveRoutine,
    isPaused,
    isRunning,
    runtimeState,
    routineRemainingSeconds,
    taskRemainingSeconds,
    timeOffsetMs,
    completeRoutine,
    initializeRealtime,
    loadActive,
    loadSync,
    pauseRoutine,
    resumeRoutine,
    skipRoutine,
    startRoutine,
    stopRoutine,
    teardownRealtime,
  }
})
