<template>
  <div class="home">
    <v-card class="mx-auto my-4" max-width="800">
      <v-card-title class="text-h4">
        Welcome to Routine Cloud
      </v-card-title>
      <v-card-text>
        <p class="text-body-1">
          Routine Cloud is a platform for managing your daily routines and tasks in the cloud.
          Stay organized and productive with our easy-to-use interface.
        </p>
        <v-divider class="my-4"></v-divider>
        <v-row>
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Create Routines</v-card-title>
              <v-card-text>
                Create custom routines for your daily activities.
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Track Progress</v-card-title>
              <v-card-text>
                Track your progress and stay motivated.
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Sync Across Devices</v-card-title>
              <v-card-text>
                Access your routines from any device.
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary">
          Get Started
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'HomeView',
  components: {
  }
}
</script>