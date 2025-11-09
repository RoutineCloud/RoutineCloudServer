<script setup lang="ts">
import {computed, ref} from 'vue'
import {library} from '@fortawesome/fontawesome-svg-core'

const props = defineProps<{
  label?: string
}>()

const icon_name = defineModel()

const emit = defineEmits<{
  (e: 'select', value: string): void
}>()

// local menu state
const open = ref(false)
const search = ref('')


// Note: main.js registers the entire solid pack via `library.add(fas)`.
// We can access the definitions to list all available icon names.
const ALL_SOLID_ICON_NAMES: string[] = Object.keys((library as any).definitions?.fas ?? {})
  .sort((a: string, b: string) => a.localeCompare(b))

// Expose as a computed to keep the same type as before
const iconNames = computed(() => ALL_SOLID_ICON_NAMES)

const filteredIcons = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = iconNames.value
  if (!q) return list
  return list.filter((n) => n.toLowerCase().includes(q))
})

const currentIcon = computed(() => {
  return icon_name.value
})

function selectIcon(name: string) {
  icon_name.value = name
  emit('select', name)
  open.value = false
}
</script>

<template>
  <div class="icon-selector">
    <!-- Activator button showing the current icon -->
    <v-menu v-model="open" :close-on-content-click="false" location="bottom" offset="8">
      <template #activator="{ props: menuProps }">
        <v-btn v-bind="menuProps" size="small" variant="outlined" rounded="pill">
          <font-awesome-icon :icon="['fas', icon_name]" class="mr-2" />
          <span>{{ label ?? 'Icon' }}</span>
        </v-btn>
      </template>

      <v-card min-width="340" elevation="8">
        <v-card-title class="py-2">
          <div class="d-flex align-center" style="gap: 8px; width: 100%">
            <span class="text-subtitle-2">Select Icon</span>
            <v-spacer />
            <v-btn icon="mdi-close" variant="text" @click="open = false" size="small" />
          </div>
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="search"
            density="compact"
            variant="outlined"
            placeholder="Search icons..."
            prepend-inner-icon="mdi-magnify"
            hide-details
          />
          <div class="icon-grid mt-2">
            <v-btn
              v-for="name in filteredIcons"
              :key="name"
              variant="text"
              size="small"
              class="icon-item"
              :color="name === currentIcon ? 'primary' : undefined"
              @click="selectIcon(name)"
            >
              <font-awesome-icon :icon="['fas', name]" size="lg" />
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-menu>
  </div>
</template>

<style scoped>
.icon-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}
.icon-item {
  width: 44px;
  height: 44px;
  justify-content: center;
  align-items: center;
  display: inline-flex;
}
</style>
