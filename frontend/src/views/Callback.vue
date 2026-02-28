<template>
  <div class="callback-page d-flex justify-center align-center fill-height">
    <v-progress-circular indeterminate color="primary"></v-progress-circular>
    <div class="ml-4">Authenticating...</div>
  </div>
</template>

<script setup lang="ts">
import {onMounted} from 'vue';
import {useRouter} from 'vue-router';
import {userManager} from '@/auth';

const router = useRouter();

onMounted(async () => {
  try {
    await userManager.signinCallback();
    router.replace('/');
  } catch (err) {
    console.error('Login callback failed:', err);
    router.replace('/login');
  }
});
</script>

<style scoped>
.callback-page {
  height: 100vh;
}
</style>
