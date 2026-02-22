<template>
  <v-container fill-height>
    <v-row align="center" justify="center">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        <div class="mt-4 text-h6">Logging you in...</div>
        <v-alert v-if="error" type="error" class="mt-4">{{ error }}</v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {useUserStore} from '@/stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const error = ref<string | null>(null);

onMounted(async () => {
  const code = route.query.code as string;
  const state = route.query.state as string;

  if (!code) {
    error.value = 'No authorization code found.';
    return;
  }

  if (await userStore.handleCallback(code)) {
    // If we have a state, we might want to use it for redirecting back, 
    // but for the basic SPA flow, we just go to Home.
    router.replace('/');
  } else {
    error.value = userStore.error || 'Failed to complete login.';
  }
});
</script>
