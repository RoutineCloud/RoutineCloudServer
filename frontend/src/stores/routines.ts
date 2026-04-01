import {defineStore} from 'pinia'
import {computed, ref} from 'vue'
import {
  AccessLevel,
  RoutineCreate,
  RoutineRead,
  Routines,
  RoutineShareRead,
  RoutineTaskAdd,
  RoutineUpdate,
  TaskInRoutineRead
} from '@/api'

export const useRoutinesStore = defineStore('routines', () => {
  // State
  const routines = ref<RoutineRead[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const shares = ref<Record<number, RoutineShareRead[]>>({})

  // Getters
  const all = computed(() => routines.value)
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

  async function moveItem(routineId: number, position: number, direction: 'up' | 'down') {
    const { data: tasks } = await Routines.routinesTasksList({ path: { routine_id: routineId } })
    const current = tasks.find(t => t.position === position)
    if (!current) return routines.value.find(r => r.id === routineId)!

    const newPos = direction === 'up' ? position - 1 : position + 1
    if (newPos < 1 || newPos > tasks.length) return routines.value.find(r => r.id === routineId)!

    await Routines.routinesTasksRemove({ path: { routine_id: routineId, position } })
    const { data } = await Routines.routinesTasksAdd({
      path: { routine_id: routineId },
      body: { task_id: current.id, position: newPos },
    })
    setRoutineTasks(routineId, data)
    return routines.value.find(r => r.id === routineId)!
  }

  async function duplicateItem(routineId: number, position: number) {
    const { data: tasks } = await Routines.routinesTasksList({ path: { routine_id: routineId } })
    const current = tasks.find(t => t.position === position)
    if (!current) return routines.value.find(r => r.id === routineId)!
    const { data } = await Routines.routinesTasksAdd({
      path: { routine_id: routineId },
      body: { task_id: current.id, position: current.position + 1 },
    })
    setRoutineTasks(routineId, data)
    return routines.value.find(r => r.id === routineId)!
  }

  // Sharing
  async function loadShares(routineId: number) {
    const { data } = await Routines.routinesSharesList({ path: { routine_id: routineId } })
    shares.value[routineId] = data
    return data
  }

  async function shareRoutine(routineId: number, userId: number, accessLevel: AccessLevel = AccessLevel.READ) {
    const { data } = await Routines.routinesSharesCreate({
      path: { routine_id: routineId },
      body: { user_id: userId, access_level: accessLevel }
    })
    if (!shares.value[routineId]) shares.value[routineId] = []
    shares.value[routineId].push(data)
    return data
  }

  async function updateShare(routineId: number, userId: number, accessLevel: AccessLevel) {
    const { data } = await Routines.routinesSharesUpdate({
      path: { routine_id: routineId, user_id: userId },
      body: { access_level: accessLevel }
    })
    const idx = shares.value[routineId]?.findIndex(s => s.user_id === userId)
    if (idx !== undefined && idx !== -1) {
      shares.value[routineId][idx] = data
    }
    return data
  }

  async function unshareRoutine(routineId: number, userId: number) {
    await Routines.routinesSharesDelete({ path: { routine_id: routineId, user_id: userId } })
    if (shares.value[routineId]) {
      shares.value[routineId] = shares.value[routineId].filter(s => s.user_id !== userId)
    }
  }

  return {
    // State
    routines,
    loading,
    error,
    shares,

    // Getters
    all,
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
    loadShares,
    shareRoutine,
    updateShare,
    unshareRoutine
  }
})
