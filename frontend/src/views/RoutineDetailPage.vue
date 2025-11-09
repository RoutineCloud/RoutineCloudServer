<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import {useRoutinesStore} from '@/stores/routines'
import {useTasksStore} from '@/stores/tasks'
import RoutineTaskList from '@/components/RoutineTaskList.vue'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'
import TaskPickerDialog from '@/components/TaskPickerDialog.vue'

const route = useRoute()
const routinesStore = useRoutinesStore()
const tasksStore = useTasksStore()

const routineId = computed(() => Number(route.params.id))
const routine = computed(() => routinesStore.byId(routineId.value).value)

const selectedItemId = ref<string | undefined>(undefined)
const showPicker = ref(false)

onMounted(async () => {
  await Promise.all([tasksStore.load(), routinesStore.load()])
  if (routine.value && routine.value.tasks.length > 0) {
    selectedItemId.value = routine.value.tasks[0].id
  }
})

watch(routine, (r) => {
  if (r && r.tasks.length > 0 && !selectedItemId.value) {
    selectedItemId.value = r.tasks[0].id
  }
})

const selectedItem = computed(() => routine.value?.tasks.find(i => i.id === selectedItemId.value))
const selectedTask = computed(() => selectedItem.value ? tasksStore.byId(selectedItem.value.id).value : undefined)
const totalMinutes = computed(() => routinesStore.totalMinutes(routineId.value).value)

function onAddTask() { showPicker.value = true }
async function onPickTask(taskId: number) {
  showPicker.value = false
  if (!routine.value) return
  const r = await routinesStore.addItem(routineId.value, { taskId })
  const added = r.tasks[r.tasks.length - 1]
  selectedItemId.value = added.id
}

async function onUpdateInstance(patch: any) {
  if (!selectedItem.value) return
  await routinesStore.updateItem(routineId.value, selectedItem.value.id, patch)
}

async function onRemoveItem(id: number) {
  await routinesStore.removeItem(routineId.value, id)
  if (selectedItemId.value === id) selectedItemId.value = routine.value?.tasks[0]?.id
}

async function onDuplicateItem(id: number) {
  const r = await routinesStore.duplicateItem(routineId.value, id)
  const idx = r.tasks.findIndex(i => i.id === id)
  const next = r.tasks[idx+1]
  if (next) selectedItemId.value = next.id
}

async function onMove(id: number, dir: 'up'|'down') {
  await routinesStore.moveItem(routineId.value, id, dir as any)
}
</script>

<template>
  <div>
    <template v-if="routine">
      <v-row>
        <v-col cols="12" md="5">
          <v-card>
            <v-card-title class="d-flex align-center" style="gap: 8px">
              <div class="text-h6">{{ routine.name }}</div>
              <v-spacer></v-spacer>
              <div class="text-medium-emphasis">Total: {{ totalMinutes }}m</div>
            </v-card-title>
            <v-card-text>
              <RoutineTaskList
                :items="routine.tasks"
                :tasks="tasksStore.tasks"
                v-model="selectedItemId"
                @add="onAddTask"
                @remove="onRemoveItem"
                @duplicate="onDuplicateItem"
                @move="onMove"
              />
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="7">
          <v-card>
            <v-card-title class="text-h6">Details</v-card-title>
            <v-card-text>
              <div v-if="selectedItem && selectedTask">
                <TaskDetailPanel
                  mode="instance"
                  :instance="selectedItem"
                  @update-instance="onUpdateInstance"
                />
              </div>
              <div v-else class="text-medium-emphasis">Select a task instance...</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <TaskPickerDialog v-model="showPicker" :tasks="tasksStore.tasks" @select="onPickTask" />
    </template>

    <template v-else>
      <v-alert type="warning" title="Not found">Routine not found.</v-alert>
    </template>
  </div>
</template>
