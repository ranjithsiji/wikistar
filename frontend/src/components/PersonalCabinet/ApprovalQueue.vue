<template>
  <div>
    <h4>Editathon Approval Queue</h4>
    <div v-if="loading" class="text-center">
      <div class="spinner-border"></div>
    </div>
    <div v-else-if="pendingEditathons.length === 0" class="alert alert-success">
      No editathons pending approval.
    </div>
    <div v-else class="list-group">
      <div v-for="editathon in pendingEditathons" :key="editathon.id" class="list-group-item">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <h5>{{ editathon.name }}</h5>
            <p class="mb-1">{{ editathon.description }}</p>
            <small class="text-muted">
              Created by: {{ editathon.creator }} | 
              {{ formatDate(editathon.createdAt) }}
            </small>
          </div>
          <div class="btn-group">
            <button @click="approveEditathon(editathon.id)" class="btn btn-sm btn-success">Approve</button>
            <button @click="rejectEditathon(editathon.id)" class="btn btn-sm btn-danger">Reject</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const pendingEditathons = ref([])
const loading = ref(true)

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}

function approveEditathon(id) {
  if (confirm('Approve this editathon?')) {
    // API call to approve
    pendingEditathons.value = pendingEditathons.value.filter(e => e.id !== id)
  }
}

function rejectEditathon(id) {
  if (confirm('Reject this editathon?')) {
    // API call to reject
    pendingEditathons.value = pendingEditathons.value.filter(e => e.id !== id)
  }
}

onMounted(async () => {
  // Load pending editathons from API
  setTimeout(() => {
    pendingEditathons.value = [
      {
        id: 5,
        name: 'Cultural Heritage Month',
        description: 'Documenting cultural heritage sites',
        creator: 'User123',
        createdAt: '2024-03-15'
      },
      {
        id: 6,
        name: 'Environmental Awareness',
        description: 'Articles about environmental issues',
        creator: 'EcoWarrior',
        createdAt: '2024-03-10'
      }
    ]
    loading.value = false
  }, 1000)
})
</script>