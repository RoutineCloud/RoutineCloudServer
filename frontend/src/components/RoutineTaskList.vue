<script setup lang="ts">
import {ref} from 'vue'
import {TaskRead} from "@/api";
import {formatSecondsToTime} from '@/utils/time'

const props = defineProps<{tasks: TaskRead[]}>()
const selected_task_id = defineModel<number>()

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'remove', id: number): void
  (e: 'duplicate', id: number): void
  (e: 'move', id: number, dir: 'up'|'down'): void
  (e: 'add'): void
}>()

const q = ref('')

function select(id: number) {
  selected_task_id.value = id
  emit('select', id)
}
</script>

<template>
  <div>
    <div class="d-flex mb-2" style="gap: 8px">
      <v-text-field v-model="q" label="Search in routine" density="compact" hide-details clearable></v-text-field>
      <v-btn color="primary" @click="$emit('add')">Add Task</v-btn>
    </div>
    <v-list density="compact">
      <v-list-item v-for="r in tasks" :key="r.id" :active="r.id===selected_task_id" @click="select(r.id)">
        <v-list-item-title>
          <font-awesome-icon :icon="['fas', r.icon_name]" class="mr-2" />
          {{ r.name }} <span class="text-medium-emphasis">- {{ formatSecondsToTime(r.duration) }}</span>
        </v-list-item-title>
        <template #append>
          <v-btn icon="mdi-arrow-up" size="small" variant="text" @click.stop="$emit('move', r.id, 'up')"></v-btn>
          <v-btn icon="mdi-arrow-down" size="small" variant="text" @click.stop="$emit('move', r.id, 'down')"></v-btn>
          <v-btn icon="mdi-content-copy" size="small" variant="text" @click.stop="$emit('duplicate', r.id)"></v-btn>
          <v-btn icon="mdi-delete" size="small" variant="text" @click.stop="$emit('remove', r.id)"></v-btn>
        </template>
      </v-list-item>
      <v-list-item v-if="tasks.length===0">
        <v-list-item-title class="text-medium-emphasis">No tasks in this routine</v-list-item-title>
      </v-list-item>
    </v-list>
  </div>
</template>
