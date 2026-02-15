<script setup lang="ts">
import {computed, ref} from 'vue'
import {useRoutinesStore} from '@/stores/routines'

interface Routine { id: number; name: string }

const props = defineProps<{ routines: Routine[]; modelValue?: number }>()
const emit = defineEmits<{ (e: 'update:modelValue', id: number): void; (e: 'select', id: number): void; (e: 'delete', id: number): void; (e: 'create'): void }>()

const q = ref('')
const filtered = computed(() => {
  const s = q.value.trim().toLowerCase()
  if (!s) return props.routines
  return props.routines.filter(r => r.name.toLowerCase().includes(s))
})

function select(id: number) {
  emit('update:modelValue', id)
  emit('select', id)
}

// Start routine handling
const routinesStore = useRoutinesStore()
const startingId = ref<number | null>(null)
async function startRoutine(id: number) {
  if (startingId.value !== null) return
  startingId.value = id
  try {
    await routinesStore.start(id)
  } catch (e) {
    console.error('Failed to start routine', e)
  } finally {
    startingId.value = null
  }
}
</script>

<template>
  <div>
    <div class="d-flex mb-2" style="gap: 8px">
      <v-text-field v-model="q" label="Search routines" density="compact" hide-details clearable></v-text-field>
      <v-btn color="primary" @click="$emit('create')">New</v-btn>
    </div>
    <v-list density="compact">
      <v-list-item v-for="r in filtered" :key="r.id" :active="r.id===modelValue" @click="select(r.id)">
        <v-list-item-title>{{ r.name }}</v-list-item-title>
        <template #append>
          <v-btn
            icon="mdi-play"
            size="small"
            variant="text"
            :loading="startingId===r.id"
            :disabled="startingId===r.id"
            @click.stop="startRoutine(r.id)"
            :title="'Start routine'"
          />
          <v-btn icon="mdi-delete" size="small" variant="text" @click.stop="$emit('delete', r.id)"></v-btn>
        </template>
      </v-list-item>
      <v-list-item v-if="filtered.length===0">
        <v-list-item-title class="text-medium-emphasis">No routines</v-list-item-title>
      </v-list-item>
    </v-list>
  </div>
</template>
