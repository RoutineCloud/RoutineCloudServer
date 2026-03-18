<script setup lang="ts">
import {computed, ref} from 'vue'
import {TaskRead} from "@/api";
import {formatSecondsToTime} from '@/utils/time'

const props = defineProps<{ tasks: TaskRead[];}>()
const emit = defineEmits<{
  (e: 'select', id: number): void;
  (e: 'delete', id: number): void;
  (e: 'create'): void
}>()

const selected_task_id = defineModel<number>()

const q = ref('')
const filtered = computed(() => {
  const s = q.value.trim().toLowerCase()
  if (!s) return props.tasks
  return props.tasks.filter(t => t.name.toLowerCase().includes(s))
})

function select(id: number) {
  selected_task_id.value = id
  emit('select', id)
}
</script>

<template>
  <div>
    <div class="d-flex mb-2" style="gap: 8px">
      <v-text-field v-model="q" label="Search tasks" density="compact" hide-details clearable></v-text-field>
      <v-btn color="primary" @click="$emit('create')">New</v-btn>
    </div>
    <v-list density="compact">
      <v-list-item v-for="t in filtered" :key="t.id" :active="t.id===modelValue" @click="select(t.id)">
        <v-list-item-title>
          <font-awesome-icon :icon="['fas', t.icon_name]" class="mr-2" />
          {{ t.name }} <span class="text-medium-emphasis">- {{ formatSecondsToTime(t.duration) }}</span>
        </v-list-item-title>
        <template #append>
          <v-btn icon="mdi-delete" size="small" variant="text" @click.stop="$emit('delete', t.id)"></v-btn>
        </template>
      </v-list-item>
      <v-list-item v-if="filtered.length===0">
        <v-list-item-title class="text-medium-emphasis">No tasks</v-list-item-title>
      </v-list-item>
    </v-list>
  </div>
</template>
