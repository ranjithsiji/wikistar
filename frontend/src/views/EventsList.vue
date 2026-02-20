<template>
  <div class="events-page container my-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="fw-bold">Browse Events</h1>
      <router-link to="/create" v-if="store.user" class="btn btn-primary d-flex align-items-center gap-2">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Create Editathon
      </router-link>
    </div>

    <!-- Search / Filter (optional, could just be local search) -->
    <div class="filters-card card mb-4 shadow-sm border-0">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <input 
              v-model="searchQuery" 
              type="text" 
              class="form-control" 
              placeholder="Search by event name or project..." 
            />
          </div>
          <div class="col-md-3">
            <select v-model="statusFilter" class="form-select">
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="draft">Pending Approval</option>
              <option value="finished">Finished</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else class="card shadow-sm border-0 table-card">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>Event Name</th>
              <th>Project</th>
              <th>Status</th>
              <th>Dates</th>
              <th class="text-end text-nowrap">👨‍👩‍👧‍👦 Users</th>
              <th class="text-end text-nowrap">📝 Articles</th>
              <th class="text-end text-nowrap">✅ Marks</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="event in filteredEvents" :key="event.id">
              <td class="fw-bold fs-6">
                <router-link :to="`/editathon/${event.code || event.id}`" class="text-decoration-none">
                  {{ event.name }}
                </router-link>
              </td>
              <td>
                <span class="badge bg-secondary rounded-pill fw-normal">{{ event.project_domain || 'Multiple' }}</span>
              </td>
              <td>
                <span class="status-badge" :class="getStatusClass(event)">
                  {{ getStatusText(event) }}
                </span>
              </td>
              <td class="small text-muted text-nowrap">
                {{ formatDate(event.startDate) }} - {{ formatDate(event.endDate) }}
              </td>
              <td class="text-end fw-bold">{{ event.user_count?.toLocaleString() || 0 }}</td>
              <td class="text-end fw-bold">{{ event.article_count?.toLocaleString() || 0 }}</td>
              <td class="text-end fw-bold text-success">{{ event.marks_count?.toLocaleString() || 0 }}</td>
            </tr>
            <tr v-if="filteredEvents.length === 0">
              <td colspan="7" class="text-center py-5 text-muted">
                No events found matching your criteria.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { store } from '../store'

const events = ref([])
const loading = ref(true)
const error = ref('')
const searchQuery = ref('')
const statusFilter = ref('')

onMounted(async () => {
  try {
    const res = await axios.get('/api/editathons')
    events.value = res.data
  } catch (err) {
    error.value = 'Failed to load events. Please try again later.'
    console.error(err)
  } finally {
    loading.value = false
  }
})

const filteredEvents = computed(() => {
  return events.value.filter(event => {
    // text search
    const query = searchQuery.value.toLowerCase()
    const matchesQuery = 
      (event.name || '').toLowerCase().includes(query) || 
      (event.project_domain || '').toLowerCase().includes(query)
      
    if (!matchesQuery) return false
    
    // status filter
    if (statusFilter.value) {
      if (statusFilter.value === 'finished') {
        return new Date(event.endDate) < new Date()
      } else if (statusFilter.value === 'active') {
        return event.status === 'active' && new Date(event.endDate) >= new Date()
      } else if (statusFilter.value === 'draft') {
        return event.status === 'draft' || event.status === 'pending'
      }
    }
    
    return true
  })
})

function formatDate(isoStr) {
  if (!isoStr) return 'TBA'
  const date = new Date(isoStr)
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function getStatusClass(event) {
  const isFinished = new Date(event.endDate) < new Date()
  if (isFinished) return 'status-finished'
  if (event.status === 'active') return 'status-active'
  if (event.status === 'draft' || event.status === 'pending') return 'status-draft'
  if (event.status === 'rejected') return 'status-rejected'
  return 'status-other'
}

function getStatusText(event) {
  const isFinished = new Date(event.endDate) < new Date()
  if (isFinished) return 'Finished'
  if (event.status === 'active') return 'Active'
  if (event.status === 'draft' || event.status === 'pending') return 'Pending Approval'
  if (event.status === 'rejected') return 'Rejected'
  return 'Archived'
}
</script>

<style scoped>
.events-page {
  font-family: 'Inter', system-ui, sans-serif;
  color: #111827;
}

.table-card {
  border-radius: 12px;
  overflow: hidden;
}

.table {
  color: #374151;
}

.table th {
  font-size: 0.8rem;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: #6b7280;
  border-bottom-width: 1px;
  padding: 16px;
}

.table td {
  padding: 16px;
  vertical-align: middle;
}

.status-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
}

.status-finished { background: #f3f4f6; color: #4b5563; }
.status-active   { background: #dcfce7; color: #166534; }
.status-draft    { background: #fef3c7; color: #92400e; }
.status-rejected { background: #fee2e2; color: #991b1b; }
.status-other    { background: #f3f4f6; color: #6b7280; }

.filters-card {
  border-radius: 10px;
}

a.text-decoration-none {
  color: #2563eb;
  transition: color 0.15s;
}
a.text-decoration-none:hover {
  text-decoration: underline !important;
  color: #1d4ed8;
}
</style>
