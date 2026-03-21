<script setup lang="ts">
import {ref} from 'vue'
import {useUserStore} from '@/stores'
import {Users} from '@/api'

const userStore = useUserStore()
const uploadingProfilePic = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const onProfilePicChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  uploadingProfilePic.value = true

  try {
    // Highly compress image using canvas
    const compressedBase64 = await compressImage(file, 150, 150, 0.6)
    await Users.usersUpdateMe({ body: { profile_picture: compressedBase64 } })
    // Update local store
    if (userStore.user) {
      userStore.user.profile_picture = compressedBase64
    }
  } catch (e) {
    console.error('Failed to update profile picture:', e)
  } finally {
    uploadingProfilePic.value = false
  }
}

const compressImage = (file: File, maxWidth: number, maxHeight: number, quality: number): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = (event) => {
      const img = new Image()
      img.src = event.target?.result as string
      img.onload = () => {
        const canvas = document.createElement('canvas')
        let width = img.width
        let height = img.height

        if (width > height) {
          if (width > maxWidth) {
            height *= maxWidth / width
            width = maxWidth
          }
        } else {
          if (height > maxHeight) {
            width *= maxHeight / height
            height = maxHeight
          }
        }

        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        ctx?.drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', quality))
      }
      img.onerror = reject
    }
    reader.onerror = reject
  })
}
</script>

<template>
  <div>
    <div class="d-flex align-center mb-6">
      <v-avatar size="100" class="mr-6" color="grey-lighten-2">
        <v-img v-if="userStore.user?.profile_picture" :src="userStore.user.profile_picture" alt="Profile Picture"></v-img>
        <v-icon v-else icon="mdi-account" size="64"></v-icon>
      </v-avatar>
      <div>
        <div class="text-h6">{{ userStore.user?.username }}</div>
        <v-btn
          size="small"
          variant="outlined"
          class="mt-2"
          @click="fileInput?.click()"
          :loading="uploadingProfilePic"
        >
          Change Picture
        </v-btn>
        <input
          type="file"
          ref="fileInput"
          style="display: none"
          accept="image/*"
          @change="onProfilePicChange"
        >
      </div>
    </div>

    <div class="text-h6 mb-4">User Profile</div>
    <div class="mb-4">
      <div class="text-caption text-grey">Username</div>
      <div class="text-body-1">{{ userStore.user?.username }}</div>
    </div>
    <div class="mb-4">
      <div class="text-caption text-grey">Email</div>
      <div class="text-body-1">{{ userStore.user?.email }}</div>
    </div>
    <div class="mb-4">
      <div class="text-caption text-grey">Friend Code</div>
      <div class="text-body-1 font-weight-bold primary--text">{{ userStore.user?.friend_code }}</div>
      <div class="text-caption text-grey">Share this code with others to let them add you as a friend.</div>
    </div>
    <div class="mb-4">
      <div class="text-caption text-grey">User ID</div>
      <div class="text-body-1">{{ userStore.user?.id }}</div>
    </div>
    <div class="mb-4">
      <div class="text-caption text-grey">Admin Status</div>
      <div class="text-body-1">{{ userStore.user?.is_superuser ? 'Administrator' : 'Regular User' }}</div>
    </div>
  </div>
</template>
