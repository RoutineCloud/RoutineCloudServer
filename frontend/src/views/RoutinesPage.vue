<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoutinesStore} from '@/stores/routines'
import {useRouter} from 'vue-router'
import RoutineList from '@/components/RoutineList.vue'

const router = useRouter()
const routinesStore = useRoutinesStore()
const selected = ref<number | undefined>(undefined)

onMounted(async () => {
  await routinesStore.load()
})

async function onCreate() {
  const r = await routinesStore.create({ name: 'New Routine', items: [] })
  selected.value = r.id
}

async function onDelete(id: number) {
  await routinesStore.remove(id)
  if (selected.value === id) selected.value = undefined
}

function onSelect(id: number) {
  router.push(`/routines/${id}`)
}
</script>

<template>
  <div>
    <v-card class="mx-auto" max-width="900">
      <v-card-title class="d-flex align-center" style="gap: 8px">
        <div class="text-h5">Routines</div>
        <v-spacer></v-spacer>
      </v-card-title>
      <v-card-text>
        <RoutineList :routines="routinesStore.all"
                     v-model="selected"
                     @create="onCreate"
                     @delete="onDelete"
                     @select="onSelect"
        />
      </v-card-text>
    </v-card>
  </div>
</template>
