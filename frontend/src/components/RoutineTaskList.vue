<script setup lang="ts">
import {computed, ref} from 'vue'

interface Item { id: number; taskId: string; minutesOverride?: number | null; note?: string }
interface Task { id: number; name: string; defaultMinutes: number; icon?: string }

const props = defineProps<{ items: Item[]; tasks: Task[]; modelValue?: string }>()
const emit = defineEmits<{
  (e: 'update:modelValue', id: number): void
  (e: 'select', id: number): void
  (e: 'remove', id: number): void
  (e: 'duplicate', id: number): void
  (e: 'move', id: number, dir: 'up'|'down'): void
  (e: 'add'): void
}>()

const q = ref('')
const rows = computed(() => {
  const s = q.value.trim().toLowerCase()
  const decorated = props.items.map(it => {
    const t = props.tasks.find(t => t.id === it.taskId)
    const base = t?.defaultMinutes ?? 0
    const minutes = it.minutesOverride != null ? it.minutesOverride : base
    return { id: it.id, name: t?.name || '(missing task)', icon: t?.icon, minutes }
  })
  if (!s) return decorated
  return decorated.filter(r => r.name.toLowerCase().includes(s))
})

function select(id: string) {
  emit('update:modelValue', id)
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
      <v-list-item v-for="r in rows" :key="r.id" :active="r.id===modelValue" @click="select(r.id)">
        <v-list-item-title>
          <v-icon size="small" class="mr-2">{{ r.icon || 'mdi-checkbox-blank-circle-outline' }}</v-icon>
          {{ r.name }} <span class="text-medium-emphasis">· {{ r.minutes }}m</span>
        </v-list-item-title>
        <template #append>
          <v-btn icon="mdi-arrow-up" size="small" variant="text" @click.stop="$emit('move', r.id, 'up')"></v-btn>
          <v-btn icon="mdi-arrow-down" size="small" variant="text" @click.stop="$emit('move', r.id, 'down')"></v-btn>
          <v-btn icon="mdi-content-copy" size="small" variant="text" @click.stop="$emit('duplicate', r.id)"></v-btn>
          <v-btn icon="mdi-delete" size="small" variant="text" @click.stop="$emit('remove', r.id)"></v-btn>
        </template>
      </v-list-item>
      <v-list-item v-if="rows.length===0">
        <v-list-item-title class="text-medium-emphasis">No tasks in this routine</v-list-item-title>
      </v-list-item>
    </v-list>
  </div>
</template>
