<template>
  <div class="user-management">
    <h3 class="mb-4">User Management</h3>

    <div v-if="loading" class="d-flex justify-content-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td class="fw-bold">{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="badge" 
                :class="{
                  'bg-danger': user.role === 'admin',
                  'bg-info text-dark': user.role === 'coordinator',
                  'bg-warning text-dark': user.role === 'jury',
                  'bg-secondary': user.role === 'user' || user.role === 'participant'
                }">
                {{ user.role }}
              </span>
            </td>
            <td>
              <select class="form-select form-select-sm d-inline-block w-auto" v-model="user._newRole">
                <option value="admin">Admin</option>
                <option value="coordinator">Coordinator</option>
                <option value="jury">Jury</option>
                <option value="user">User</option>
              </select>
              <button 
                class="btn btn-sm btn-primary ms-2" 
                @click="updateUserRole(user)"
                :disabled="user.role === user._newRole || !user._newRole">
                Save
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const users = ref([])
const loading = ref(true)
const error = ref(null)

async function fetchUsers() {
  try {
    loading.value = true
    const res = await axios.get('/api/users')
    users.value = res.data.map(u => ({ ...u, _newRole: u.role === 'participant' ? 'user' : u.role }))
  } catch (e) {
    error.value = 'Failed to load users.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function updateUserRole(user) {
  try {
    const res = await axios.put(`/api/users/${user.id}/role`, { role: user._newRole })
    if (res.data.success) {
      user.role = user._newRole
      alert(`Updated role for ${user.username} to ${user._newRole}`)
    }
  } catch (e) {
    alert('Failed to update user role.')
    console.error(e)
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management {
  font-family: Arial, sans-serif;
}
</style>
