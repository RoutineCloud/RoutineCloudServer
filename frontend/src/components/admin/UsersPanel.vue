<script setup lang="ts">
import {onMounted, reactive, ref} from 'vue'
import {type UserCreate, type UserRead, Users} from '@/api'

const users = ref<UserRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const dialog = ref(false)
const form = reactive<UserCreate>({
  email: '',
  username: '',
  password: '',
  is_active: true,
  is_superuser: false,
})
const creating = ref(false)
const createError = ref<string | null>(null)

async function loadUsers() {
  loading.value = true
  error.value = null
  try {
    const {data, error: err} = await Users.usersList()
    if (err) {
      error.value = (err as any)?.detail || 'Failed to load users'
      return
    }
    users.value = data as UserRead[]
  } catch (e: any) {
    error.value = e?.message || 'Network error'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.email = ''
  form.username = ''
  form.password = ''
  form.is_active = true
  form.is_superuser = false
}

async function createUser() {
  creating.value = true
  createError.value = null
  try {
    const {error: err} = await Users.usersCreate({
      body: {
        email: form.email,
        username: form.username,
        password: form.password,
        is_active: form.is_active,
        is_superuser: form.is_superuser,
      }
    })
    if (err) {
      createError.value = (err as any)?.detail || 'Failed to create user'
      return
    }
    dialog.value = false
    resetForm()
    await loadUsers()
  } catch (e: any) {
    createError.value = e?.message || 'Network error'
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <v-card>
    <v-card-title class="d-flex align-center" style="gap: 8px">
      <span class="text-h6">Users</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="dialog = true" prepend-icon="mdi-account-plus">Add User</v-btn>
      <v-btn :loading="loading" icon="mdi-refresh" variant="text" @click="loadUsers" />
    </v-card-title>
    <v-card-text>
      <v-alert v-if="error" type="error" density="comfortable">{{ error }}</v-alert>
      <v-skeleton-loader v-else-if="loading" type="table" />
      <div v-else>
        <v-table density="comfortable">
          <thead>
          <tr>
            <th>Email</th>
            <th>Username</th>
            <th>Active</th>
            <th>Superuser</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="u in users" :key="u.email">
            <td>{{ u.email }}</td>
            <td>{{ u.username }}</td>
            <td>
              <v-chip :color="u.is_active ? 'blue' : 'grey'" size="small" label variant="outlined">
                {{ u.is_active ? 'Yes' : 'No' }}
              </v-chip>
            </td>
            <td>
              <v-chip :color="u.is_superuser ? 'red' : 'grey'" size="small" label variant="outlined">
                {{ u.is_superuser ? 'Yes' : 'No' }}
              </v-chip>
            </td>
          </tr>
          </tbody>
        </v-table>
        <v-alert v-if="!users.length" type="info" class="mt-4" variant="tonal">No users found.</v-alert>
      </div>
    </v-card-text>
  </v-card>

  <v-dialog v-model="dialog" max-width="520">
    <v-card>
      <v-card-title class="text-h6">Add User</v-card-title>
      <v-card-text>
        <v-text-field v-model="form.email" label="Email" type="email" required />
        <v-text-field v-model="form.username" label="Username" required />
        <v-text-field v-model="form.password" label="Password" type="password" required />
        <div class="d-flex" style="gap: 12px">
          <v-switch v-model="form.is_active" label="Active" color="primary" inset />
          <v-switch v-model="form.is_superuser" label="Superuser" color="primary" inset />
        </div>
        <v-alert v-if="createError" type="error" density="comfortable" class="mt-2">{{ createError }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
        <v-btn color="primary" :loading="creating" @click="createUser">Create</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
