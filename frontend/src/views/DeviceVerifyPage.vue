<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useUserStore} from '@/stores/user'
import {Authentication} from "@/api";

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const userCode = ref('')
const submitting = ref(false)
const message = ref<string | null>(null)
const errormessage = ref<string | null>(null)

onMounted(() => {
  const q = (route.query.user_code as string) || ''
  if (q) userCode.value = q
})

const goToLogin = () => {
  const redirect = encodeURIComponent(route.fullPath);
  router.push(`/login?redirect=${redirect}`);
};

async function submit() {
  message.value = null
  errormessage.value = null
  if (!userCode.value || userCode.value.trim().length < 4) {
    errormessage.value = 'Please enter the code shown on your device.'
    return
  }

  submitting.value = true
  try {
    const {data, error} = await Authentication.verifyDeviceCodeApiOauthDeviceVerifyPost({
      body: {
        user_code: userCode.value.trim(),
        name: "Test device",
        approve: true
      }
    })
    if (error) {
      errormessage.value = (error?.detail || 'Verification failed')
      return
    }
    message.value = 'Device linked successfully.'
  } catch (e: any) {
    errormessage.value = e?.message || 'Network error'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="d-flex justify-center">
    <div v-if="!userStore.isAuthenticated" class="text-center my-5">
      <p class="text-body-1 mb-5">
        You need to sign in to your Routine Cloud account before linking with your device.
      </p>
      <v-btn color="primary" size="large" @click="goToLogin">
        Sign In
      </v-btn>
    </div>
    <v-card v-else class="mx-auto mt-8" max-width="560">
      <v-card-title class="text-h6">Link your device</v-card-title>
      <v-card-text>
        <p>Enter the code shown on your device to link it with your account.</p>

        <div v-if="!userStore.isAuthenticated" class="mb-3">
          <v-alert type="warning" title="Login required" density="comfortable">
            Please <RouterLink to="/login">log in</RouterLink> to continue.
          </v-alert>
        </div>

        <v-text-field
          v-model="userCode"
          label="Device code"
          placeholder="e.g. A1B2C3D4"
          variant="outlined"
          density="comfortable"
          :disabled="submitting"
        />
        <div class="mt-2 d-flex" style="gap: 8px">
          <v-btn color="primary" :loading="submitting" :disabled="!userCode" @click="submit">Verify</v-btn>
          <v-btn variant="text" @click="userCode = ''">Clear</v-btn>
        </div>

        <div class="mt-4" v-if="message">
          <v-alert type="success" :text="message" />
        </div>
        <div class="mt-4" v-if="errormessage">
          <v-alert type="error" :text="errormessage" />
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>
