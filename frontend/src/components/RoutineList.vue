<script setup lang="ts">
import {computed, ref} from 'vue'
import {useRoutinesStore} from '@/stores/routines'
import {RoutineRead} from '@/api'
import ShareRoutineDialog from '@/components/ShareRoutineDialog.vue'

const props = defineProps<{ routines: RoutineRead[]; modelValue?: number }>()
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
    await routinesStore.loadActiveStatus()
  }
}

// Sharing
const showShareDialog = ref(false)
const shareRoutine = ref<RoutineRead | null>(null)
function openShare(r: RoutineRead) {
  shareRoutine.value = r
  showShareDialog.value = true
}
</script>

<template>
  <div>
    <ShareRoutineDialog v-if="shareRoutine" v-model="showShareDialog" :routine="shareRoutine" />
    <div class="d-flex mb-2" style="gap: 8px">
      <v-text-field v-model="q" label="Search routines" density="compact" hide-details clearable></v-text-field>
      <v-btn color="primary" @click="$emit('create')">New</v-btn>
    </div>
    <v-list density="compact">
      <v-list-item v-for="r in filtered" :key="r.id" :active="r.id===modelValue" @click="select(r.id)">
        <template #prepend v-if="r.access_level && r.access_level !== 'owner'">
          <v-icon icon="mdi-account-group" size="small" color="primary" class="mr-2" title="Shared with me"></v-icon>
        </template>
        <v-list-item-title>{{ r.name }}</v-list-item-title>
        <template #append>
          <v-btn
            v-if="r.access_level === 'owner'"
            icon="mdi-share-variant"
            size="small"
            variant="text"
            @click.stop="openShare(r)"
            title="Share routine"
          />
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
