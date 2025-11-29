<template>
  <div class="created-editathons">
    <div class="header-section">
      <div>
        <h3>🛠️ Editathons Created by You</h3>
        <p class="subtitle">Manage and track your editathon submissions</p>
      </div>
      <router-link to="/create" class="btn btn-create">
        <span class="btn-icon">+</span> Create New Editathon
      </router-link>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading your editathons...</p>
    </div>

    <div v-else-if="editathons.length === 0" class="empty-state">
      <div class="empty-icon">📝</div>
      <h4>No Editathons Yet</h4>
      <p>You haven't created any editathons. Start by creating your first one!</p>
      <router-link to="/create" class="btn btn-primary">Create Your First Editathon</router-link>
    </div>

    <div v-else class="editathons-grid">
      <div v-for="editathon in editathons" :key="editathon.id" class="editathon-card">
        <div class="card-header-status">
          <span class="status-badge" :class="`status-${editathon.status}`">
            <span class="status-icon">{{ getStatusIcon(editathon.status) }}</span>
            {{ getStatusText(editathon.status) }}
          </span>
          <span class="created-date">{{ formatDate(editathon.created) }}</span>
        </div>

        <div class="card-content">
          <h4 class="editathon-title">{{ editathon.name }}</h4>
          <p class="editathon-description">{{ editathon.description }}</p>
          
          <div class="editathon-meta">
            <div class="meta-item">
              <span class="meta-label">Language:</span>
              <span class="meta-value">{{ editathon.wiki_language || 'ml' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Duration:</span>
              <span class="meta-value">{{ formatDateRange(editathon.startDate, editathon.endDate) }}</span>
            </div>
          </div>

          <div v-if="editathon.status === 'pending'" class="pending-note">
            ⏳ Awaiting admin approval
          </div>
          <div v-if="editathon.status === 'rejected'" class="rejection-note">
            ❌ Rejected: {{ editathon.rejection_reason || 'Please contact admin' }}
          </div>
        </div>

        <div class="card-actions">
          <router-link 
            v-if="editathon.status === 'approved'" 
            :to="`/editathon/${editathon.id}`" 
            class="btn btn-manage">
            Manage Editathon
          </router-link>
          <button 
            v-else-if="editathon.status === 'pending'" 
            class="btn btn-secondary" 
            disabled>
            Pending Approval
          </button>
          <button 
            v-else-if="editathon.status === 'rejected'" 
            @click="editEditathon(editathon)" 
            class="btn btn-warning">
            Edit & Resubmit
          </button>
          <button 
            @click="deleteEditathon(editathon.id)" 
            class="btn btn-danger-outline"
            title="Delete editathon">
            🗑️
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
      method: 'DELETE'
    })
    
    if (response.ok) {
      editathons.value = editathons.value.filter(e => e.id !== id)
      alert('Editathon deleted successfully')
    } else {
      alert('Failed to delete editathon')
    }
  } catch (error) {
    console.error('Error deleting editathon:', error)
    alert('Error deleting editathon')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    // Load created editathons from API
    const response = await fetch(`http://localhost:5000/api/user/${props.user}/editathons`)
    if (response.ok) {
      editathons.value = await response.json()
    } else {
      // Fallback to mock data
      editathons.value = [
        {
          id: 3,
          name: 'Women in STEM 2024',
          description: 'Highlighting women in science and technology',
          wiki_language: 'ml',
          status: 'approved',
          created: '2024-01-15',
          startDate: '2024-02-01',
          endDate: '2024-02-28'
        },
        {
          id: 4,
          name: 'Local History Project',
          description: 'Documenting local historical figures',
          wiki_language: 'ml',
          status: 'pending',
          created: '2024-03-01',
          startDate: '2024-03-15',
          endDate: '2024-04-15'
        }
      ]
    }
  } catch (error) {
    console.error('Error loading editathons:', error)
    editathons.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.created-editathons {
  padding: 1rem;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-section h3 {
  margin: 0;
  font-size: 1.8rem;
  color: #2c3e50;
}

.subtitle {
  color: #7f8c8d;
  margin: 0.25rem 0 0 0;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-create {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-create:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  font-size: 1.2rem;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h4 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #7f8c8d;
  margin-bottom: 1.5rem;
}

.editathons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.editathon-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.editathon-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-4px);
}

.card-header-status {
  padding: 1rem;
  background: #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #e9ecef;
}

.status-badge {
  padding: 0.4rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.status-pending {
  background-color: #fff3cd;
  color: #856404;
}

.status-approved {
  background-color: #d4edda;
  color: #155724;
}

.status-rejected {
  background-color: #f8d7da;
  color: #721c24;
}

.status-draft {
  background-color: #e2e3e5;
  color: #383d41;
}

.created-date {
  font-size: 0.85rem;
  color: #6c757d;
}

.card-content {
  padding: 1.5rem;
}

.editathon-title {
  font-size: 1.3rem;
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.editathon-description {
  color: #7f8c8d;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.editathon-meta {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.meta-label {
  color: #7f8c8d;
  font-weight: 600;
}

.meta-value {
  color: #2c3e50;
}

.pending-note, .rejection-note {
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.9rem;
  margin-top: 1rem;
}

.pending-note {
  background-color: #fff3cd;
  color: #856404;
}

.rejection-note {
  background-color: #f8d7da;
  color: #721c24;
}

.card-actions {
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  display: flex;
  gap: 0.5rem;
  border-top: 2px solid #e9ecef;
}

.btn-manage {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  justify-content: center;
}

.btn-secondary {
  flex: 1;
  background-color: #6c757d;
  color: white;
  justify-content: center;
}

.btn-warning {
  flex: 1;
  background-color: #ffc107;
  color: #212529;
  justify-content: center;
}

.btn-danger-outline {
  background: white;
  color: #dc3545;
  border: 2px solid #dc3545;
  padding: 0.5rem 1rem;
}

.btn-danger-outline:hover {
  background-color: #dc3545;
  color: white;
}

@media (max-width: 768px) {
  .editathons-grid {
    grid-template-columns: 1fr;
  }
  
  .header-section {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .btn-create {
    width: 100%;
    justify-content: center;
  }
}
</style>