<script setup lang="ts">
import {onMounted, reactive, ref} from 'vue'
import {Admin, type OAuth2ClientRead, type OAuth2ClientUpdate} from '@/api'

const clients = ref<OAuth2ClientRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const editDialog = ref(false)
const selectedClient = ref<OAuth2ClientRead | null>(null)
const editForm = reactive<OAuth2ClientUpdate & { metadataStr: string }>({
  client_id: '',
  client_secret: '',
  metadataStr: '{}'
})
const updating = ref(false)
const updateError = ref<string | null>(null)

async function loadClients() {
  loading.value = true
  error.value = null
  try {
    const {data, error: err} = await Admin.adminListOauthClients()
    if (err) {
      error.value = (err as any)?.detail || 'Failed to load OAuth clients'
      return
    }
    clients.value = data as OAuth2ClientRead[]
  } catch (e: any) {
    error.value = e?.message || 'Network error'
  } finally {
    loading.value = false
  }
}

function openEdit(client: OAuth2ClientRead) {
  selectedClient.value = client
  editForm.client_id = client.client_id
  editForm.client_secret = '' // Don't show existing secret
  editForm.metadataStr = JSON.stringify(client.client_metadata || {}, null, 2)
  editDialog.value = true
}

async function updateClient() {
  if (!selectedClient.value) return
  updating.value = true
  updateError.value = null
  try {
    let metadata = {}
    try {
      metadata = JSON.parse(editForm.metadataStr)
    } catch (e) {
      updateError.value = 'Invalid JSON in metadata'
      updating.value = false
      return
    }

    const {error: err} = await Admin.adminUpdateOauthClient({
      path: { client_id: selectedClient.value.id },
      body: {
        client_id: editForm.client_id,
        client_secret: editForm.client_secret || undefined,
        client_metadata: metadata
      }
    })
    if (err) {
      updateError.value = (err as any)?.detail || 'Failed to update client'
      return
    }
    editDialog.value = false
    await loadClients()
  } catch (e: any) {
    updateError.value = e?.message || 'Network error'
  } finally {
    updating.value = false
  }
}

onMounted(() => {
  loadClients()
})
</script>

<template>
  <v-card>
    <v-card-title class="d-flex align-center" style="gap: 8px">
      <span class="text-h6">OAuth Clients</span>
      <v-spacer></v-spacer>
      <v-btn :loading="loading" icon="mdi-refresh" variant="text" @click="loadClients" />
    </v-card-title>
    <v-card-text>
      <v-alert v-if="error" type="error" density="comfortable">{{ error }}</v-alert>
      <v-skeleton-loader v-else-if="loading" type="table" />
      <div v-else>
        <v-table density="comfortable">
          <thead>
          <tr>
            <th>Client ID</th>
            <th>Name (Metadata)</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="c in clients" :key="c.id">
            <td>{{ c.client_id }}</td>
            <td>{{ (c.client_metadata as any)?.client_name || '-' }}</td>
            <td>
              <v-btn icon="mdi-pencil" size="small" variant="text" color="primary" @click="openEdit(c)" />
            </td>
          </tr>
          </tbody>
        </v-table>
        <v-alert v-if="!clients.length" type="info" class="mt-4" variant="tonal">No OAuth clients found.</v-alert>
      </div>
    </v-card-text>
  </v-card>

  <v-dialog v-model="editDialog" max-width="600">
    <v-card>
      <v-card-title class="text-h6">Edit OAuth Client</v-card-title>
      <v-card-text>
        <v-text-field v-model="editForm.client_id" label="Client ID" required />
        <v-text-field
            v-model="editForm.client_secret"
            label="Client Secret (Leave empty to keep current)"
            hint="The secret will not be shown once saved."
            persistent-hint
            type="password"
        />
        <v-textarea
            v-model="editForm.metadataStr"
            label="Client Metadata (JSON)"
            rows="10"
            required
            hint="Standard fields: client_name, grant_types, response_types, scope, redirect_uris"
            persistent-hint
        />
        <v-alert v-if="updateError" type="error" density="comfortable" class="mt-4">{{ updateError }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="editDialog = false">Cancel</v-btn>
        <v-btn color="primary" :loading="updating" @click="updateClient">Save</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
