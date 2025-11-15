<script setup lang="ts">
// Static informational page using Vuetify layout
const updatedOn = '2025-11-12'
</script>

<template>
  <div class="about">
    <v-container class="my-6">
      <v-row>
        <v-col cols="12" md="8" class="mx-auto">
          <v-card>
            <v-card-title class="text-h4">About Routine Cloud</v-card-title>
            <v-card-text>
              <p class="text-body-1">
                Routine Cloud helps you design, start, and coordinate daily routines across your devices. 
                It combines a friendly editor for routines with real‑time device control via WebSockets.
              </p>

              <v-divider class="my-6" />

              <div class="mb-4">
                <div class="text-h5 mb-2">The Idea</div>
                <p class="text-body-1">
                  Build repeatable flows for your morning, study sessions, workouts, or evening wind‑downs. 
                  Each routine is a sequence of tasks with durations. When you press play, connected devices receive the command and can react instantly.
                </p>
              </div>

              <v-divider class="my-6" />

              <div class="mb-4">
                <div class="text-h5 mb-2">About the Programmer</div>
                <p class="text-body-1">
                  This project is crafted by the developer behind Routine Cloud.
                  <!-- TODO: Replace the placeholder below with your own short bio -->
                  I am a software engineer passionate about automation, great UX, and reliable cloud services.
                </p>
              </div>

              <v-divider class="my-6" />

              <div class="mb-2">
                <div class="text-h5 mb-2">Impressum / Legal Notice</div>
                <p class="text-body-2 text-medium-emphasis mb-4">
                  The following information complies with legal requirements for provider identification. Replace placeholders with your actual details.
                </p>
                <v-card variant="outlined" class="mb-4">
                  <v-card-text>
                    <div class="mb-2"><strong>Responsible entity:</strong> <!-- TODO: Name / Company --> Your Name or Company</div>
                    <div class="mb-2"><strong>Address:</strong> <!-- TODO: Street, No., ZIP, City, Country --> Street 1, 12345 City, Country</div>
                    <div class="mb-2"><strong>Contact:</strong> <!-- TODO: Email, Phone --> email@example.com, +00 000 000000</div>
                    <div class="mb-2"><strong>VAT ID (if applicable):</strong> <!-- TODO: VAT No. --> DE123456789</div>
                    <div class="mb-2"><strong>Commercial register (if applicable):</strong> <!-- TODO: Court / Register No. --> Local Court ABC, HRB 123456</div>
                    <div class="mb-2"><strong>Represented by:</strong> <!-- TODO: Managing director / owner --> Firstname Lastname</div>
                    <div class="text-caption text-medium-emphasis">Last updated: {{ updatedOn }}</div>
                  </v-card-text>
                </v-card>
                <div class="text-body-2 text-medium-emphasis">
                  Note: If you operate this service privately and local law does not require an Impressum, remove or adapt this section accordingly. 
                  Consider adding links to your Privacy Policy and Terms of Service if available.
                </div>
              </div>

            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>