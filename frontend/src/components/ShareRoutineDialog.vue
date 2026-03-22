<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue'
import {useFriendsStore, useRoutinesStore} from '@/stores'
import {AccessLevel, RoutineRead} from '@/api'

const props = defineProps<{
  modelValue: boolean
  routine: RoutineRead
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

const friendsStore = useFriendsStore()
const routinesStore = useRoutinesStore()

const loading = ref(false)
const error = ref('')

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const shares = computed(() => routinesStore.shares[props.routine.id] || [])

const availableFriends = computed(() => {
  const sharedUserIds = new Set(shares.value.map(s => s.user_id))
  return friendsStore.friends.filter(f => !sharedUserIds.has(f.id))
})

onMounted(async () => {
  await friendsStore.fetchFriends()
})

watch(() => props.routine.id, async (newId) => {
  if (newId && isOpen.value) {
    loading.value = true
    try {
      await routinesStore.loadShares(newId)
    } finally {
      loading.value = false
    }
  }
}, { immediate: true })

watch(isOpen, async (val) => {
  if (val && props.routine.id) {
    loading.value = true
    try {
      await routinesStore.loadShares(props.routine.id)
    } finally {
      loading.value = false
    }
  }
})

async function shareWithFriend(friendId: number) {
  loading.value = true
  try {
    await routinesStore.shareRoutine(props.routine.id, friendId, 'read')
  } catch (e: any) {
    error.value = e.body?.detail || 'Failed to share routine'
  } finally {
    loading.value = false
  }
}

async function removeShare(userId: number) {
  loading.value = true
  try {
    await routinesStore.unshareRoutine(props.routine.id, userId)
  } catch (e: any) {
    error.value = e.body?.detail || 'Failed to remove share'
  } finally {
    loading.value = false
  }
}

async function updateAccessLevel(userId: number, level: AccessLevel) {
  loading.value = true
  try {
    await routinesStore.updateShare(props.routine.id, userId, level)
  } catch (e: any) {
    error.value = e.body?.detail || 'Failed to update share'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-dialog v-model="isOpen" max-width="500px">
    <v-card>
      <v-card-title class="d-flex align-center">
        <span>Share "{{ routine.name }}"</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="isOpen = false"></v-btn>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = ''">
          {{ error }}
        </v-alert>

        <div v-if="shares.length > 0">
          <div class="text-subtitle-2 mb-2">Already shared with:</div>
          <v-list density="compact">
            <v-list-item v-for="share in shares" :key="share.user_id" class="px-0">
              <template v-slot:prepend>
                <v-avatar size="32" class="mr-2">
                  <v-img v-if="share.profile_picture" :src="share.profile_picture"></v-img>
                  <v-icon v-else icon="mdi-account"></v-icon>
                </v-avatar>
              </template>
              <v-list-item-title>{{ share.username }}</v-list-item-title>
              <template v-slot:append>
                <v-select
                  :model-value="share.access_level"
                  @update:model-value="(val) => updateAccessLevel(share.user_id, val)"
                  :items="['read', 'write']"
                  density="compact"
                  variant="plain"
                  hide-details
                  style="width: 80px"
                  class="mr-2"
                ></v-select>
                <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="removeShare(share.user_id)"></v-btn>
              </template>
            </v-list-item>
          </v-list>
        </div>

        <v-divider v-if="shares.length > 0" class="my-4"></v-divider>

        <div class="text-subtitle-2 mb-2">Share with a friend:</div>
        <v-list v-if="availableFriends.length > 0" density="compact">
          <v-list-item v-for="friend in availableFriends" :key="friend.id" class="px-0">
            <template v-slot:prepend>
              <v-avatar size="32" class="mr-2">
                <v-img v-if="friend.profile_picture" :src="friend.profile_picture"></v-img>
                <v-icon v-else icon="mdi-account"></v-icon>
              </v-avatar>
            </template>
            <v-list-item-title>{{ friend.username }}</v-list-item-title>
            <template v-slot:append>
              <v-btn color="primary" variant="text" @click="shareWithFriend(friend.id)">Share</v-btn>
            </template>
          </v-list-item>
        </v-list>
        <div v-else class="text-center text-medium-emphasis py-4">
          No more friends to share with.
        </div>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="isOpen = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
