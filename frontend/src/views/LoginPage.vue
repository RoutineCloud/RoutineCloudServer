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
                    <v-form ref="form" v-model="valid" @submit.prevent="login">
                      <v-text-field
                        v-model="email"
                        label="Email"
                        prepend-inner-icon="mdi-email"
                        type="email"
                        required
                      ></v-text-field>
                      <v-text-field
                        v-model="password"
                        label="Password"
                        prepend-inner-icon="mdi-lock"
                        :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                        :type="showPassword ? 'text' : 'password'"
                        @click:append-inner="showPassword = !showPassword"
                        required
                      ></v-text-field>
                      <v-btn
                        block
                        color="primary"
                        size="large"
                        type="submit"
                        :loading="loading"
                        :disabled="!valid"
                      >
                        Sign In
                      </v-btn>
                    </v-form>
                    <v-alert
                        closable
                        v-model="error"
                        v-if="error"
                        type="error">{{ error }}
                    </v-alert>
                  </v-card-text>
                  <v-divider class="my-3"></v-divider>
                  <v-card-actions class="justify-center">
                    <div class="text-center">
                      <div class="mb-3">Don't have an account?</div>
                      <v-btn variant="outlined" color="primary">
                        Create Account
                      </v-btn>
                    </div>
                  </v-card-actions>
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
import {ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {useUserStore} from '@/stores';


const router = useRouter();
const route = useRoute();
const valid = ref(false);
const loading = ref(false);
const email = ref('');
const password = ref('');
const showPassword = ref(false);
const error = ref('');
const userStore = useUserStore()

const login = async () => {
  if (!valid.value) return;
  
  loading.value = true;

  if(await userStore.authLogin(email.value, password.value)) {
    const redirectPath = route.query.redirect as string;
    
    if (redirectPath) {
      // If we have a redirect path (e.g. from an external OAuth request or navigation guard)
      if(redirectPath.startsWith('http')) {
        window.location.assign(redirectPath);
      } else {
        router.push(redirectPath);
      }
    } else {
      // Direct login to the application - no longer need OAuth2 Code flow for ourselves
      router.push('/');
    }
  } else {
    error.value = 'Invalid credentials';
  }
  loading.value = false;
};
</script>

<style scoped>
.login-page {
  height: 100vh;
}
</style>