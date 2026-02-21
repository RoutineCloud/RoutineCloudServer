<script setup lang="ts">
import {ref} from 'vue'
import {Users} from '@/api'

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const success = ref(false)

const showCurrent = ref(false)
const showNew = ref(false)
const showConfirm = ref(false)

async function changePassword() {
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'New passwords do not match'
    return
  }

  if (newPassword.value.length < 1) {
    error.value = 'New password cannot be empty'
    return
  }

  loading.value = true
  error.value = null
  success.value = false

  try {
    const { error: apiError } = await Users.usersChangePassword({
      body: {
        current_password: currentPassword.value,
        new_password: newPassword.value
      }
    })

    if (apiError) {
      error.value = (apiError as any).detail || 'Failed to change password'
    } else {
      success.value = true
      currentPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
    }
  } catch (err) {
    error.value = 'An unexpected error occurred'
    console.error(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-card variant="flat">
    <v-card-title class="text-h6 px-0">Change Password</v-card-title>
    <v-card-text class="px-0">
      <v-form @submit.prevent="changePassword">
        <v-text-field
          v-model="currentPassword"
          label="Current Password"
          :type="showCurrent ? 'text' : 'password'"
          :append-inner-icon="showCurrent ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showCurrent = !showCurrent"
          required
          density="comfortable"
        ></v-text-field>

        <v-text-field
          v-model="newPassword"
          label="New Password"
          :type="showNew ? 'text' : 'password'"
          :append-inner-icon="showNew ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showNew = !showNew"
          required
          density="comfortable"
        ></v-text-field>

        <v-text-field
          v-model="confirmPassword"
          label="Confirm New Password"
          :type="showConfirm ? 'text' : 'password'"
          :append-inner-icon="showConfirm ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showConfirm = !showConfirm"
          required
          density="comfortable"
        ></v-text-field>

        <v-alert v-if="error" type="error" class="mb-4" density="comfortable" variant="tonal">
          {{ error }}
        </v-alert>

        <v-alert v-if="success" type="success" class="mb-4" density="comfortable" variant="tonal">
          Password changed successfully!
        </v-alert>

        <div class="d-flex justify-end">
          <v-btn
            type="submit"
            color="primary"
            :loading="loading"
          >
            Update Password
          </v-btn>
        </div>
      </v-form>
    </v-card-text>
  </v-card>
</template>
