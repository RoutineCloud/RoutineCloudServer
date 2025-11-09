<script setup lang="ts">
import {computed, ref, watch} from 'vue'

interface Instance { id?: string; taskId: string; minutesOverride?: number | null; note?: string }

const props = defineProps<{
  mode: 'global' | 'instance'
  task?: Task
  instance?: Instance
  baseMinutes?: number
}>()

const emit = defineEmits<{
  (e: 'save-global', patch: Partial<Task>): void
  (e: 'update-instance', patch: Partial<Instance>): void
}>()

// Local form state
const name = ref('')
const defaultMinutes = ref<number | null>(null)
const icon = ref('')
const description = ref('')

const minutesOverride = ref<number | null>(null)
const note = ref('')

watch(() => props.task, (t) => {
  if (props.mode === 'global' && t) {
    name.value = t.name
    defaultMinutes.value = t.defaultMinutes
    icon.value = t.icon || ''
    description.value = t.description || ''
  }
}, { immediate: true })

watch(() => props.instance, (i) => {
  if (props.mode === 'instance' && i) {
    minutesOverride.value = i.minutesOverride ?? null
    note.value = i.note || ''
  }
}, { immediate: true })

const effectiveMinutes = computed(() => {
  if (props.mode !== 'instance') return null
  const base = props.baseMinutes ?? 0
  return minutesOverride.value != null ? minutesOverride.value : base
})
</script>

<template>
  <div>
    <template v-if="mode==='global'">
      <h3 class="text-h6 mb-3">Task</h3>
      <v-text-field v-model="name" label="Name" class="mb-2" />
      <v-text-field v-model.number="defaultMinutes" type="number" label="Default minutes" class="mb-2" />
      <v-text-field v-model="icon" label="Icon (mdi-*)" class="mb-2" />
      <v-textarea v-model="description" label="Description" rows="4" />
      <div class="mt-3 d-flex" style="gap: 8px">
        <v-btn color="primary" @click="emit('save-global', { name, defaultMinutes: Number(defaultMinutes), icon, description })">Save</v-btn>
      </div>
    </template>

    <template v-else>
      <h3 class="text-h6 mb-3">Task Instance</h3>
      <v-text-field v-model.number="minutesOverride" type="number" label="Minutes override (optional)" class="mb-2" clearable />
      <div class="text-medium-emphasis mb-2">Effective minutes: {{ effectiveMinutes }}<span v-if="baseMinutes != null"> (base {{ baseMinutes }}m)</span></div>
      <v-textarea v-model="note" label="Note" rows="4" />
      <div class="mt-3 d-flex" style="gap: 8px">
        <v-btn color="primary" @click="emit('update-instance', { minutesOverride: minutesOverride!=null?Number(minutesOverride):null, note })">Save</v-btn>
      </div>
    </template>
  </div>
</template>
