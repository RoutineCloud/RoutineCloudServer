<script setup lang="ts">
import {computed, ref} from 'vue'

interface Task { id: string; name: string; defaultMinutes: number; icon?: string }

const props = defineProps<{ tasks: Task[]; modelValue?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', id: string): void; (e: 'select', id: string): void; (e: 'delete', id: string): void; (e: 'create'): void }>()

const q = ref('')
const filtered = computed(() => {
  const s = q.value.trim().toLowerCase()
  if (!s) return props.tasks
  return props.tasks.filter(t => t.name.toLowerCase().includes(s))
})

function select(id: string) {
  emit('update:modelValue', id)
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
          <v-icon size="small" class="mr-2">{{ t.icon || 'mdi-checkbox-blank-circle-outline' }}</v-icon>
          {{ t.name }} <span class="text-medium-emphasis">· {{ t.defaultMinutes }}m</span>
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
