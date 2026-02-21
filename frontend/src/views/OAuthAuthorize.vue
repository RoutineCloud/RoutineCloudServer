<template>
  <div class="oauth-authorize">
    <v-container>
      <v-row justify="center">
        <v-col cols="12" sm="10" md="8" lg="6">
          <v-card class="elevation-5 mt-10">
            <v-card-title class="text-center text-h5 pt-5">
              <v-icon size="large" color="primary" class="mr-2">mdi-link-variant</v-icon>
              Link Your Alexa Account
            </v-card-title>
            
            <v-card-text>
              <div v-if="!userStore.isAuthenticated" class="text-center my-5">
                <p class="text-body-1 mb-5">
                  You need to sign in to your Routine Cloud account before linking with Alexa.
                </p>
                <v-btn color="primary" size="large" @click="goToLogin">
                  Sign In
                </v-btn>
              </div>
              
              <div v-else>
                <v-alert
                  v-if="error"
                  type="error"
                  class="mb-4"
                >
                  {{ error }}
                </v-alert>
                
                <div class="text-center mb-5">
                  <v-img
                    src="https://m.media-amazon.com/images/G/01/mobile-apps/dex/alexa/alexa-skills-kit/tutorials/quiz-game/alexa-logo._TTH_.png"
                    max-width="150"
                    class="mx-auto mb-4"
                  ></v-img>
                  
                  <p class="text-body-1 mb-4">
                    <strong>{{ clientName }}</strong> is requesting permission to access your Routine Cloud account.
                  </p>
                  
                  <p class="text-body-1 mb-4">
                    This will allow you to control your routines and devices using Alexa voice commands.
                  </p>
                  
                  <v-divider class="my-5"></v-divider>
                  
                  <p class="text-subtitle-1 font-weight-bold mb-2">
                    The following permissions will be granted:
                  </p>
                  
                  <v-list density="compact" class="bg-transparent">
                    <v-list-item>
                      <template v-slot:prepend>
                        <v-icon color="success">mdi-check-circle</v-icon>
                      </template>
                      <v-list-item-title>View your routines</v-list-item-title>
                    </v-list-item>
                    <v-list-item>
                      <template v-slot:prepend>
                        <v-icon color="success">mdi-check-circle</v-icon>
                      </template>
                      <v-list-item-title>Control your devices</v-list-item-title>
                    </v-list-item>
                    <v-list-item>
                      <template v-slot:prepend>
                        <v-icon color="success">mdi-check-circle</v-icon>
                      </template>
                      <v-list-item-title>Execute your routines</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </div>
                
                <v-card-actions class="justify-center pb-5">
                  <v-btn
                    color="error"
                    variant="outlined"
                    class="mr-4"
                    @click="denyAuthorization"
                    :disabled="loading"
                  >
                    Deny
                  </v-btn>
                  <v-btn
                    color="primary"
                    @click="authorizeAccount"
                    :loading="loading"
                  >
                    Allow
                  </v-btn>
                </v-card-actions>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {Oauth2} from "@/api";

import {useUserStore} from '@/stores/user.ts'

const userStore = useUserStore()
const route = useRoute();
const router = useRouter();

// State variables
const clientName = ref('Amazon Alexa');
const loading = ref(false);
const error = ref(null);

// Get OAuth parameters from URL
const clientId = route.query.client_id;
const redirectUri = route.query.redirect_uri;
const state = route.query.state;
const responseType = route.query.response_type;
const scope = route.query.scope;
const challenge = route.query.code_challenge;
const challengeMethod = route.query.code_challenge_method;

onMounted(() => {
  // Validate OAuth parameters
  validateOAuthParameters();
});

const validateOAuthParameters = () => {
  if (!clientId || !redirectUri || !responseType) {
    error.value = 'Invalid authorization request. Missing required parameters.';
  }
};

const authorizeAccount = async () => {
  loading.value = true;
  
  try {

    const {data, error} = await Oauth2.authorizeJsonApiOauthAuthJsonPost(
        {
          query: {
            client_id:clientId,
            redirect_uri:redirectUri,
            response_type:responseType,
            scope:scope,
            state:state,
            code_challenge:challenge,
            code_challenge_method:challengeMethod,
          }
        }
    )

    console.log(data)
    window.location.assign(data.redirect_to);

  } catch (err) {
    console.error('Authorization failed:', err);
    error.value = err.message || 'Failed to authorize. Please try again.';
  } finally {
    loading.value = false;
  }
};

const denyAuthorization = () => {
  // Redirect back to Alexa with an error
  if (redirectUri) {
    const redirectUrl = new URL(redirectUri);
    redirectUrl.searchParams.append('error', 'access_denied');
    if (state) {
      redirectUrl.searchParams.append('state', state);
    }
    
    window.location.href = redirectUrl.toString();
  } else {
    // If no redirect URI, just go back to home
    router.push('/');
  }
};
const goToLogin = () => {
  const redirect = encodeURIComponent(route.fullPath);
  router.push(`/login?redirect=${redirect}`);
};
</script>

<style scoped>
.oauth-authorize {
  min-height: 100vh;
  padding: 20px 0;
}
</style>