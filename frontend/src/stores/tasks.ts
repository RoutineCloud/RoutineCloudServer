import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { Tasks } from '@/api'
import type { TaskRead, TaskCreate, TaskUpdate } from '@/api'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<TaskRead[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const all = computed(() => tasks.value)
  const byId = (id: number) => computed(() => tasks.value.find(t => t.id === id))

  async function load() {
    loading.value = true
    error.value = null
    try {
      const { data } = await Tasks.tasksList()
      tasks.value = data
    } catch (e) {
      error.value = 'Failed to load tasks'
    } finally {
      loading.value = false
    }
  }

  async function create(partial: TaskCreate) {
    const { data } = await Tasks.tasksCreate({ body: partial })
    tasks.value.push(data)
    return data
  }

  async function update(id: number, patch: TaskUpdate) {
    const { data } = await Tasks.tasksUpdate({ path: { task_id: id }, body: patch })
    const idx = tasks.value.findIndex(x => x.id === id)
    if (idx !== -1) tasks.value[idx] = data
    return data
  }

  async function remove(id: number) {
    await Tasks.tasksDelete({ path: { task_id: id } })
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  return { tasks, loading, error, all, byId, load, create, update, remove }
})
