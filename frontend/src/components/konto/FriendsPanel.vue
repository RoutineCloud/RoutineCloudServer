<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useFriendsStore, useUserStore} from '@/stores'

const userStore = useUserStore()
const friendsStore = useFriendsStore()

const friendCodeToAdd = ref('')
const addingFriend = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const fetchFriends = async () => {
  await friendsStore.fetchFriends()
}

const addFriend = async () => {
  if (!friendCodeToAdd.value) return
  addingFriend.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const msg = await friendsStore.addFriend(friendCodeToAdd.value)
    successMessage.value = msg
    friendCodeToAdd.value = ''
  } catch (e: any) {
    errorMessage.value = e.body?.detail || friendsStore.error || 'Failed to add friend'
  } finally {
    addingFriend.value = false
  }
}

const acceptRequest = async (id: number) => {
  try {
    await friendsStore.acceptRequest(id)
  } catch (e: any) {
    errorMessage.value = e.body?.detail || friendsStore.error || 'Failed to accept friend request'
  }
}

const declineRequest = async (id: number) => {
  try {
    await friendsStore.declineRequest(id)
  } catch (e: any) {
    errorMessage.value = e.body?.detail || friendsStore.error || 'Failed to decline friend request'
  }
}

const removeFriend = async (id: number) => {
  try {
    await friendsStore.removeFriend(id)
  } catch (e: any) {
    errorMessage.value = e.body?.detail || friendsStore.error || 'Failed to remove friend'
  }
}

onMounted(() => {
  if (userStore.user) {
    fetchFriends()
  }
})
</script>

<template>
  <div>
    <div class="text-h6 mb-4">Friends</div>
    
    <div class="d-flex mb-6">
      <v-text-field
        v-model="friendCodeToAdd"
        label="Add Friend by Code"
        placeholder="E.g. ABCDEFGH"
        variant="outlined"
        density="comfortable"
        hide-details
        class="mr-2"
        @keyup.enter="addFriend"
      ></v-text-field>
      <v-btn
        color="primary"
        height="48"
        @click="addFriend"
        :loading="addingFriend"
      >
        Add
      </v-btn>
    </div>
    <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4" closable @click:close="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>
    <v-alert v-if="successMessage" type="success" variant="tonal" class="mb-4" closable @click:close="successMessage = ''">
      {{ successMessage }}
    </v-alert>

    <div v-if="friendsStore.friendRequests.length > 0">
      <div class="text-subtitle-1 mb-2 font-weight-bold">Friend Requests</div>
      <v-list class="mb-4 bg-grey-lighten-4 rounded">
        <v-list-item
          v-for="request in friendsStore.friendRequests"
          :key="request.id"
        >
          <template v-slot:prepend>
            <v-avatar color="grey-lighten-2">
              <v-img v-if="request.profile_picture" :src="request.profile_picture"></v-img>
              <v-icon v-else icon="mdi-account"></v-icon>
            </v-avatar>
          </template>
          <v-list-item-title>{{ request.username }}</v-list-item-title>
          <template v-slot:append>
            <v-btn
              icon="mdi-check"
              variant="text"
              color="success"
              size="small"
              class="mr-1"
              @click="acceptRequest(request.id)"
            ></v-btn>
            <v-btn
              icon="mdi-close"
              variant="text"
              color="error"
              size="small"
              @click="declineRequest(request.id)"
            ></v-btn>
          </template>
        </v-list-item>
      </v-list>
    </div>

    <v-divider class="mb-4"></v-divider>

    <div v-if="friendsStore.loading" class="text-center py-4">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
    </div>
    <div v-else-if="friendsStore.friends.length === 0" class="text-center py-4 text-grey">
      You haven't added any friends yet.
    </div>
    <v-list v-else>
      <v-list-item
        v-for="friend in friendsStore.friends"
        :key="friend.id"
        class="px-0"
      >
        <template v-slot:prepend>
          <v-avatar color="grey-lighten-2">
            <v-img v-if="friend.profile_picture" :src="friend.profile_picture"></v-img>
            <v-icon v-else icon="mdi-account"></v-icon>
          </v-avatar>
        </template>
        <v-list-item-title>{{ friend.username }}</v-list-item-title>
        <template v-slot:append>
          <v-btn
            icon="mdi-account-remove"
            variant="text"
            color="error"
            size="small"
            @click="removeFriend(friend.id)"
          ></v-btn>
        </template>
      </v-list-item>
    </v-list>
  </div>
</template>
