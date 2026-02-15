<script setup lang="ts">
import {computed, ref} from 'vue'
import {TaskRead} from "@/api";

const props = defineProps<{ modelValue: boolean; tasks: TaskRead[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void; (e: 'select', id: number): void }>()

const q = ref('')
const filtered = computed(() => {
  const s = q.value.trim().toLowerCase()
  if (!s) return props.tasks
  return props.tasks.filter(t => t.name.toLowerCase().includes(s))
})

function close() { emit('update:modelValue', false) }
</script>

<template>
  <v-dialog :model-value="modelValue" @update:modelValue="v=>emit('update:modelValue', v)" max-width="600">
    <v-card>
      <v-card-title class="d-flex" style="gap: 8px">
        <div class="text-h6">Add Task</div>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-card-title>
      <v-card-text>
        <v-text-field v-model="q" label="Search tasks" clearable hide-details class="mb-3" />
        <v-list density="compact">
          <v-list-item v-for="t in filtered" :key="t.id" @click="emit('select', t.id)">
            <v-list-item-title>
              <v-icon size="small" class="mr-2">{{ t.icon_name || 'mdi-checkbox-blank-circle-outline' }}</v-icon>
              {{ t.name }} <span class="text-medium-emphasis">· {{ t.duration }}m</span>
            </v-list-item-title>
          </v-list-item>
          <v-list-item v-if="filtered.length===0">
            <v-list-item-title class="text-medium-emphasis">No tasks</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="close">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
