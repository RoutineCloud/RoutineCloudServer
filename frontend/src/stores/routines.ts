import {defineStore} from 'pinia'
import {computed, ref} from 'vue'
import {
  ActiveRoutineStatusRead,
  RoutineControl,
  RoutineCreate,
  RoutineRead,
  Routines,
  RoutineTaskAdd,
  RoutineUpdate,
  TaskInRoutineRead
} from '@/api'

export const useRoutinesStore = defineStore('routines', () => {
  // State
  const routines = ref<RoutineRead[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeStatus = ref<ActiveRoutineStatusRead | null>(null)

  // Getters
  const all = computed(() => routines.value)
  const hasActiveRoutine = computed(() => !!activeStatus.value?.active_routine_id)
  const isActivePaused = computed(() => (activeStatus.value?.status ?? '').toLowerCase() === 'paused')
  const byId = (id: number) => computed(() => routines.value.find(r => r.id === id))
  const totalMinutes = (id: number) => computed(() => {
    const r = routines.value.find(r => r.id === id)
    if (!r || !r.tasks) return 0
    return r.tasks.reduce((sum, t) => sum + (t.duration ?? 0), 0)
  })

  // Helpers
  function setRoutineTasks(routineId: number, tasks: TaskInRoutineRead[]) {
    const idx = routines.value.findIndex(r => r.id === routineId)
    if (idx !== -1) {
      routines.value[idx] = { ...routines.value[idx], tasks }
    }
  }

  // Actions
  async function load() {
    loading.value = true
    error.value = null
    try {
      const { data } = await Routines.routinesList({ query: { include_tasks: true } })
      routines.value = data
    } catch (err) {
      console.error('Failed to load routines:', err)
      error.value = 'Failed to load routines.'
    } finally {
      loading.value = false
    }
  }

  async function create(partial: RoutineCreate) {
    const { data } = await Routines.routinesCreate({ body: partial })
    // Ensure tasks is present (backend may return [])
    const withTasks: RoutineRead = { ...data, tasks: data.tasks ?? [] }
    routines.value.push(withTasks)
    return withTasks
  }

  async function update(id: number, patch: RoutineUpdate) {
    const { data } = await Routines.routinesUpdate({ path: { routine_id: id }, body: patch })
    const idx = routines.value.findIndex(x => x.id === id)
    if (idx !== -1) routines.value[idx] = data
    return data
  }

  async function remove(id: number) {
    await Routines.routinesDelete({ path: { routine_id: id } })
    routines.value = routines.value.filter(r => r.id !== id)
  }

  async function addItem(routineId: number, item: { task_id: number; position?: number | null }) {
    const body: RoutineTaskAdd = { task_id: item.task_id, position: item.position ?? undefined }
    const { data } = await Routines.routinesTasksAdd({ path: { routine_id: routineId }, body })
    setRoutineTasks(routineId, data)
    return routines.value.find(r => r.id === routineId)!
  }

  // Not supported by API; keep signature and refresh routine state
  async function updateItem(routineId: number, _itemId: number, _patch: unknown) {
    console.warn('Routine item update not supported by API; reloading tasks instead.')
    const { data } = await Routines.routinesTasksList({ path: { routine_id: routineId } })
    setRoutineTasks(routineId, data)
    return routines.value.find(r => r.id === routineId)!
  }

  async function removeItem(routineId: number, position: number) {
    const { data } = await Routines.routinesTasksRemove({ path: { routine_id: routineId, position } })
    setRoutineTasks(routineId, data)
    return routines.value.find(r => r.id === routineId)!
  }

  async function moveItem(routineId: number, itemId: number, direction: 'up' | 'down') {
    // Load current tasks
    const { data: tasks } = await Routines.routinesTasksList({ path: { routine_id: routineId } })
    const currentIndex = tasks.findIndex(t => t.id === itemId)
    if (currentIndex === -1) return routines.value.find(r => r.id === routineId)!

    const currentPos = tasks[currentIndex].position
    const newPos = direction === 'up' ? currentPos - 1 : currentPos + 1
    if (newPos < 1 || newPos > tasks.length) return routines.value.find(r => r.id === routineId)!

    // Remove then re-add at new position
    await Routines.routinesTasksRemove({ path: { routine_id: routineId, position: currentPos } })
    const taskId = itemId
    const { data } = await Routines.routinesTasksAdd({ path: { routine_id: routineId }, body: { task_id: taskId, position: newPos } })
    setRoutineTasks(routineId, data)
    return routines.value.find(r => r.id === routineId)!
  }

  async function duplicateItem(routineId: number, itemId: number) {
    // Insert a duplicate right after the current position
    const { data: tasks } = await Routines.routinesTasksList({ path: { routine_id: routineId } })
    const current = tasks.find(t => t.id === itemId)
    if (!current) return routines.value.find(r => r.id === routineId)!
    const { data } = await Routines.routinesTasksAdd({ path: { routine_id: routineId }, body: { task_id: itemId, position: current.position + 1 } })
    setRoutineTasks(routineId, data)
    return routines.value.find(r => r.id === routineId)!
  }

  async function start(id: number) {
    await Routines.routinesStart({ path: { routine_id: id } })
  }

  async function loadActiveStatus() {
    const { data } = await Routines.routinesActiveStatus()
    activeStatus.value = data
    return data
  }

  async function pauseActive() {
    await Routines.routinesActivePause()
    await loadActiveStatus()
  }

  async function resumeActive() {
    await Routines.routinesActiveResume()
    await loadActiveStatus()
  }

  async function stopActive() {
    await RoutineControl.stopCurrentRoutineApiRoutineControlStopPost()
    await loadActiveStatus()
  }

  async function skipActive() {
    await Routines.routinesActiveSkip()
    await loadActiveStatus()
  }

  return {
    // State
    routines,
    loading,
    error,
    activeStatus,

    // Getters
    all,
    hasActiveRoutine,
    isActivePaused,
    byId,
    totalMinutes,

    // Actions
    load,
    create,
    update,
    remove,
    addItem,
    updateItem,
    removeItem,
    moveItem,
    duplicateItem,
    start,
    loadActiveStatus,
    pauseActive,
    resumeActive,
    stopActive,
    skipActive,
  }
})
