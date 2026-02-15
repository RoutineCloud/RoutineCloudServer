<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {useTasksStore} from '@/stores/tasks'
import TaskList from '@/components/TaskList.vue'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'

const tasksStore = useTasksStore()
const selectedId = ref<number | undefined>(undefined)
const selectedTask = computed(() => selectedId.value ? tasksStore.byId(selectedId.value).value : undefined)

onMounted(async () => {
  await tasksStore.load()
  if (!selectedId.value && tasksStore.tasks.length) selectedId.value = tasksStore.tasks[0].id
})

async function onCreate() {
  const t = await tasksStore.create({ name: 'New Task', duration: 5, icon_name: 'list-check', sound: 'default_sound' })
  selectedId.value = t.id
}

async function onDelete(id: number) {
  await tasksStore.remove(id)
  if (selectedId.value === id) selectedId.value = tasksStore.tasks[0]?.id
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
              <TaskDetailPanel :task="selectedTask" />
            </div>
            <div v-else class="text-medium-emphasis">Select a task...</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
