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
              <div v-if="!userStore.isAuthenticated && !isSessionAuthenticated" class="text-center my-5">
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
                  
                  <v-divider class="my-5"></v-divider>
                  
                  <p class="text-subtitle-1 font-weight-bold mb-2">
                    The following permissions will be granted:
                  </p>
                  
                  <v-list v-if="consentInfo" density="compact" class="bg-transparent">
                    <v-list-item v-for="s in consentInfo.scopes" :key="s.id">
                      <template v-slot:prepend>
                        <v-icon color="success">mdi-check-circle</v-icon>
                      </template>
                      <v-list-item-title>{{ s.name }}</v-list-item-title>
                      <v-list-item-subtitle v-if="s.description">{{ s.description }}</v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                  
                  <div v-else-if="!loading && !error" class="text-center py-4">
                    <p class="text-body-2 text-grey">No specific permissions requested.</p>
                  </div>
                  
                  <div v-else-if="loading" class="text-center py-4">
                    <v-progress-circular indeterminate color="primary"></v-progress-circular>
                    <p class="text-caption mt-2">Loading permissions...</p>
                  </div>
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
import {Auth, Oauth2} from "@/api";

import {useUserStore} from '@/stores/user.ts'

const userStore = useUserStore()
const route = useRoute();
const router = useRouter();

// State variables
const consentInfo = ref(null);
const clientName = ref('Loading...');
const loading = ref(false);
const error = ref(null);
const isSessionAuthenticated = ref(false);

// Get OAuth parameters from URL
const clientId = route.query.client_id;
const redirectUri = route.query.redirect_uri;
const state = route.query.state;
const responseType = route.query.response_type;
const scope = route.query.scope;
const challenge = route.query.code_challenge;
const challengeMethod = route.query.code_challenge_method;

onMounted(async () => {
  // Validate OAuth parameters
  validateOAuthParameters();
  
  // Check if session authenticated if not token authenticated
  if (!userStore.isAuthenticated) {
    try {
      const { data, error: meError } = await Auth.authSessionMe();
      if (!meError) {
        isSessionAuthenticated.value = true;
      }
    } catch (err) {
      console.warn('Session check failed:', err);
    }
  }

  // Fetch real consent information
  if (clientId && !error.value) {
    await fetchConsentInfo();
  }
});

const fetchConsentInfo = async () => {
  loading.value = true;
  try {
    const { data, error: fetchError } = await Oauth2.oauthGetConsentInfo({
      query: {
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: responseType,
        scope: scope,
        state: state,
        code_challenge: challenge,
        code_challenge_method: challengeMethod,
      }
    });

    if (fetchError) {
      error.value = 'Failed to load consent information.';
      clientName.value = 'Unknown Client';
    } else {
      consentInfo.value = data;
      clientName.value = data.client_name;
    }
  } catch (err) {
    console.error('Failed to fetch consent info:', err);
    error.value = 'Failed to load consent information.';
    clientName.value = 'Unknown Client';
  } finally {
    loading.value = false;
  }
};

const validateOAuthParameters = () => {
  if (!clientId || !redirectUri || !responseType) {
    error.value = 'Invalid authorization request. Missing required parameters.';
  }
};

const authorizeAccount = async () => {
  loading.value = true;
  
  try {

    const {data, error} = await Oauth2.oauthConsent(
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