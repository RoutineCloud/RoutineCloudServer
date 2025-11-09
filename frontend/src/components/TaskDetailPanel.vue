<script setup lang="ts">
import {computed, ref, watch} from 'vue'
import {useTasksStore} from '@/stores/tasks'
import IconSelector from '@/components/IconSelector.vue'
import {TaskRead} from '@/api'


const props = defineProps<{
  task?: TaskRead
}>()

const tasksStore = useTasksStore()

// Local editable state initialized from the task
const name = ref('')
const icon = ref('')
const minutes = ref<number>(0)
const seconds = ref<number>(0)

function initFromTask(t?: TaskRead | null) {
  if (!t) {
    name.value = ''
    minutes.value = 0
    seconds.value = 0
    icon.value = ''
    return
  }
  name.value = t.name ?? ''
  icon.value = t.icon_name ?? ''
  const d = t.duration ?? 0
  minutes.value = Math.floor(d / 60)
  seconds.value = d % 60
}

watch(() => props.task, (t) => initFromTask(t), { immediate: true })

// Clamp seconds to [0,59]
function normalizeTime() {
  if (seconds.value < 0) seconds.value = 0
  if (seconds.value > 59) seconds.value = 59
  if (minutes.value < 0) minutes.value = 0
}

const totalSeconds = computed(() => {
  normalizeTime()
  return (minutes.value * 60) + (seconds.value || 0)
})

const canSave = computed(() => !!props.task && name.value.trim().length > 0)

async function save() {
  if (!props.task) return
  try {
    await tasksStore.update(props.task.id, {
      name: name.value.trim(),
      duration: totalSeconds.value,
      icon_name: icon.value,
    })
  } catch (e) {
    console.error('Failed to save task:', e)
  }
}
</script>

<template>
  <div>
    <div v-if="props.task">
      <div class="d-flex align-center mb-4" style="gap: 12px">
        <IconSelector v-model="icon" label="Icon" />
        <v-text-field
          v-model="name"
          label="Name"
          variant="outlined"
          density="compact"
          hide-details
          style="max-width: 360px"
        />
      </div>

      <div class="mt-2">
        <div class="text-subtitle-2 mb-1">Time</div>
        <div class="d-flex align-center" style="gap: 8px">
          <v-text-field
            v-model.number="minutes"
            type="number"
            min="0"
            label="Minutes"
            variant="outlined"
            density="compact"
            hide-details
            style="width: 140px"
          />
          <v-text-field
            v-model.number="seconds"
            type="number"
            min="0"
            max="59"
            label="Seconds"
            variant="outlined"
            density="compact"
            hide-details
            style="width: 140px"
          />
        </div>
      </div>
      <div class="mt-4 d-flex" style="gap: 8px">
        <v-btn color="primary" :disabled="!canSave" @click="save">Save</v-btn>
      </div>
    </div>
    <div v-else class="text-medium-emphasis">No task selected.</div>
  </div>
</template>
