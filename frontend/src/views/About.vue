<template>
  <div class="about">
    <v-card class="mx-auto my-4" max-width="800">
      <v-card-title class="text-h4">
        About Routine Cloud
      </v-card-title>
      <v-card-text>
        <p class="text-body-1">
          Routine Cloud is a modern web application designed to help users manage their daily routines and tasks efficiently.
          Built with cutting-edge technologies, it provides a seamless experience across all devices.
        </p>
        
        <v-divider class="my-4"></v-divider>
        
        <h3 class="text-h5 mb-3">Technology Stack</h3>
        <v-row>
          <v-col cols="12" md="6">
            <v-card outlined>
              <v-card-title>Frontend</v-card-title>
              <v-card-text>
                <ul>
                  <li>Vue.js 3 - Progressive JavaScript Framework</li>
                  <li>Vuetify 3 - Material Design Component Framework</li>
                  <li>Vue Router - Official Router for Vue.js</li>
                  <li>Vuex - State Management Pattern + Library</li>
                </ul>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card outlined>
              <v-card-title>Backend</v-card-title>
              <v-card-text>
                <ul>
                  <li>FastAPI - Modern, Fast Web Framework for Python</li>
                  <li>SQLAlchemy - SQL Toolkit and ORM</li>
                  <li>Pydantic - Data Validation and Settings Management</li>
                  <li>Alembic - Database Migration Tool</li>
                </ul>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <v-divider class="my-4"></v-divider>
        
        <p class="text-body-1">
          This project is developed as a demonstration of modern web development practices,
          including containerization with Docker and CI/CD pipelines.
        </p>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'AboutView'
}
</script>