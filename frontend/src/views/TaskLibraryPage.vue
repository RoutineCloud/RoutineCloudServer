<script setup lang="ts">
import {onMounted, ref, computed} from 'vue'
import { useTasksStore } from '@/stores/tasks'
import TaskList from '@/components/TaskList.vue'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'

const tasksStore = useTasksStore()
const selectedId = ref<string | undefined>(undefined)
const selectedTask = computed(() => selectedId.value ? tasksStore.byId(selectedId.value).value : undefined)

onMounted(async () => {
  await tasksStore.load()
  if (!selectedId.value && tasksStore.tasks.length) selectedId.value = tasksStore.tasks[0].id
})

async function onCreate() {
  const t = await tasksStore.create({ name: 'New Task', defaultMinutes: 5 })
  selectedId.value = t.id
}

async function onDelete(id: string) {
  await tasksStore.remove(id)
  if (selectedId.value === id) selectedId.value = tasksStore.tasks[0]?.id
}

async function onSaveGlobal(patch: any) {
  if (!selectedId.value) return
  await tasksStore.update(selectedId.value, patch)
}
</script>

<template>
  <div>
    <v-row>
      <v-col cols="12" md="5">
        <v-card>
          <v-card-title class="text-h6">Tasks</v-card-title>
          <v-card-text>
            <TaskList :tasks="tasksStore.tasks" v-model="selectedId" @create="onCreate" @delete="onDelete" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="7">
        <v-card>
          <v-card-title class="text-h6">Details</v-card-title>
          <v-card-text>
            <div v-if="selectedTask">
              <TaskDetailPanel mode="global" :task="selectedTask" @save-global="onSaveGlobal" />
            </div>
            <div v-else class="text-medium-emphasis">Select a task...</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
