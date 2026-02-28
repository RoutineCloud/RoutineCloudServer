<template>
  <div class="login-page">
    <v-container fluid fill-height class="pa-0">
      <v-row no-gutters>
        <v-col cols="12" md="6" class="d-none d-md-flex bg-primary">
          <div class="d-flex flex-column justify-center align-center fill-height white--text">
            <h1 class="text-h3 font-weight-bold mb-4">Routine Cloud</h1>
            <p class="text-h6 text-center mx-10">
              Manage your daily routines and take back control over your time
            </p>
          </div>
        </v-col>
        <v-col cols="12" md="6">
          <v-container class="fill-height">
            <v-row justify="center" align="center">
              <v-col cols="12" sm="8" md="9" lg="6">
                <v-card class="elevation-12 pa-4">
                  <v-card-title class="text-center text-h5 font-weight-bold">
                    Sign In
                  </v-card-title>
                  <v-card-text>
                    <v-btn
                        block
                        color="primary"
                        size="large"
                        :loading="loading"
                        @click="login"
                      >
                        Sign In with OIDC
                    </v-btn>
                    <v-alert
                        closable
                        v-model="error"
                        v-if="error"
                        type="error"
                        class="mt-4">{{ error }}
                    </v-alert>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-container>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue';
import {useUserStore} from '@/stores';

const loading = ref(false);
const error = ref('');
const userStore = useUserStore()

onMounted(() => {
  login();
});

const login = () => {
  loading.value = true;
  userStore.login();
};
</script>

<style scoped>
.login-page {
  height: 100vh;
}
</style>