<template>
  <div class="created-section">
    <div class="section-header">
      <h2 class="section-title">Created Editathons</h2>
      <router-link to="/create" class="btn-add">
        + New Editathon
      </router-link>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading editathons...</p>
    </div>

    <div v-else-if="editathons.length === 0" class="empty-state">
      <p>You haven't created any editathons yet.</p>
      <router-link to="/create" class="link">Create your first editathon</router-link>
    </div>

    <div v-else class="editathons-list">
      <div v-for="editathon in editathons" :key="editathon.id" class="editathon-box">
        <div class="box-header">
          <h3 class="box-title">{{ editathon.name }}</h3>
          <span class="status-badge" :class="`status-${editathon.status}`">
            {{ getStatusText(editathon.status) }}
          </span>
        </div>

        <p class="box-description">{{ editathon.description }}</p>

        <div class="box-meta">
          <div class="meta-item">
            <span class="meta-label">Duration:</span>
            <span class="meta-value">{{ formatDateRange(editathon.startDate, editathon.endDate) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Language:</span>
            <span class="meta-value">{{ editathon.wiki_language || 'N/A' }}</span>
          </div>
        </div>

        <div v-if="editathon.status === 'pending'" class="note warning">
          Awaiting admin review
        </div>
        <div v-if="editathon.status === 'rejected'" class="note error">
          {{ editathon.rejection_reason || 'Rejected by admin' }}
        </div>

        <div class="box-actions">
          <router-link 
            v-if="editathon.status === 'approved' || editathon.status === 'active'" 
            :to="`/editathon/${editathon.id}`" 
            class="btn-action btn-manage">
            Manage
          </router-link>
          <router-link
            v-else-if="editathon.status === 'pending' || editathon.status === 'draft'"
            :to="`/editathon/${editathon.id}/edit`"
            class="btn-action btn-edit">
            ✏️ Edit
          </router-link>
          <router-link
            v-else-if="editathon.status === 'rejected'"
            :to="`/editathon/${editathon.id}/edit`"
            class="btn-action btn-edit">
            ✏️ Edit & Resubmit
          </router-link>
          <button 
            @click="deleteEditathon(editathon.id)" 
            class="btn-action btn-delete">
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  user: String,
  editathons: Array
})

const editathons = ref([])
const loading = ref(true)

function getStatusIcon(status) {
  const icons = {
    draft: '📝',
    pending: '⏳',
    approved: '✅',
    rejected: '❌'
  }
  return icons[status] || '📝'
}

function getStatusText(status) {
  const texts = {
    draft: 'Draft',
    pending: 'Pending Approval',
    approved: 'Approved',
    rejected: 'Rejected'
  }
  return texts[status] || status
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function formatDateRange(start, end) {
  if (!start || !end) return 'Not specified'
  return `${formatDate(start)} - ${formatDate(end)}`
}

function editEditathon(editathon) {
  router.push(`/editathon/${editathon.id}/edit`)
}

async function deleteEditathon(id) {
  if (!confirm('Are you sure you want to delete this editathon? This action cannot be undone.')) {
    return
  }

  try {
    const response = await fetch(`http://localhost:5000/api/editathon/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    })

    const result = await response.json()

    if (response.ok && result.success) {
      editathons.value = editathons.value.filter(e => e.id !== id)
    } else {
      alert('Failed to delete: ' + (result.error || 'Unknown error'))
    }
  } catch (error) {
    console.error('Error deleting editathon:', error)
    alert('Network error while deleting editathon')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const response = await fetch(`http://localhost:5000/api/personal-cabinet/${props.user}`)
    if (response.ok) {
      const data = await response.json()
      // Map backend field names to frontend expected names
      editathons.value = (data.created_editathons || []).map(e => ({
        ...e,
        startDate: e.start_date,
        endDate: e.end_date,
        wiki_language: e.language || e.wiki_language || 'N/A'
      }))
    } else {
      editathons.value = []
    }
  } catch (error) {
    console.error('Error loading created editathons:', error)
    editathons.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.created-section {
  padding: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.btn-add {
  padding: 0.7rem 1.4rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-add:hover {
  background: #5568d3;
}

.loading {
  padding: 2rem;
  text-align: center;
  background: #f9fafb;
  border: 2px dashed #e5e7eb;
  border-radius: 8px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  padding: 2rem;
  text-align: center;
  background: #f9fafb;
  border: 2px dashed #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  font-weight: 500;
}

.link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.link:hover {
  color: #5568d3;
  text-decoration: underline;
}

.editathons-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.editathon-box {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  transition: all 0.3s ease;
}

.editathon-box:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.box-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.box-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.status-badge {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-approved {
  background: #dcfce7;
  color: #166534;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-rejected {
  background: #fee2e2;
  color: #991b1b;
}

.status-draft {
  background: #f3f4f6;
  color: #4b5563;
}

.box-description {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

.box-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
  margin-bottom: 0.75rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meta-value {
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 600;
}

.note {
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.note.warning {
  background: #fef3c7;
  color: #92400e;
}

.note.error {
  background: #fee2e2;
  color: #991b1b;
}

.box-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn-action {
  padding: 0.65rem 1.2rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}

.btn-manage {
  background: #667eea;
  color: white;
}

.btn-manage:hover {
  background: #5568d3;
}

.btn-pending {
  background: #d1d5db;
  color: #6b7280;
  cursor: not-allowed;
}

.btn-edit {
  background: #fbbf24;
  color: #78350f;
}

.btn-edit:hover {
  background: #f59e0b;
}

.btn-delete {
  background: white;
  color: #dc3545;
  border: 2px solid #dc3545;
}

.btn-delete:hover {
  background: #dc3545;
  color: white;
}

@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-add {
    width: 100%;
    justify-content: center;
  }

  .box-meta {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
}
</style>