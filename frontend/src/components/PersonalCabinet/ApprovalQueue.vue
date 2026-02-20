<template>
  <div class="approval-queue">
    <div class="queue-header">
      <h3>⏳ Editathons Requiring Approval</h3>
      <span class="count-badge">{{ pendingEditathons.length }}</span>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading pending editathons...</p>
    </div>

    <div v-else-if="pendingEditathons.length === 0" class="empty-state">
      <div class="empty-icon">✓</div>
      <h4>All Caught Up!</h4>
      <p>No editathons pending approval at this time.</p>
    </div>

    <div v-else class="queue-list">
      <div v-for="editathon in pendingEditathons" :key="editathon.id" class="queue-item">
        <div class="item-header">
          <div class="item-info">
            <h4>{{ editathon.title }}</h4>
            <p class="description">{{ editathon.description }}</p>
            <div class="meta-info">
              <span class="meta-tag">👤 {{ editathon.createdBy }}</span>
              <span class="meta-tag">📅 {{ formatDate(editathon.submissionDate) }}</span>
              <span class="meta-tag">🌐 {{ editathon.wiki_language }}</span>
            </div>
          </div>
          <div class="status-badge">Pending</div>
        </div>

        <div class="item-details">
          <div class="detail-group">
            <span class="label">Project:</span>
            <span class="value">{{ editathon.project }}</span>
          </div>
          <div class="detail-group">
            <span class="label">Period:</span>
            <span class="value">{{ formatDate(editathon.startDate) }} to {{ formatDate(editathon.endDate) }}</span>
          </div>
          <div class="detail-group">
            <span class="label">Status:</span>
            <span class="value">{{ editathon.status }}</span>
          </div>
        </div>

        <div class="item-actions">
          <button @click="approveEditathon(editathon.id)" class="btn-approve">
            ✓ Approve
          </button>
          <button @click="rejectEditathon(editathon.id)" class="btn-reject">
            ✕ Reject
          </button>
          <button @click="viewDetails(editathon.id)" class="btn-view">
            View Details
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
const pendingEditathons = ref([])
const loading = ref(true)

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch (e) {
    return dateString
  }
}

async function fetchPendingEditathons() {
  try {
    loading.value = true
    const response = await fetch('/api/editathons/pending')
    if (!response.ok) throw new Error('Failed to fetch pending editathons')
    const data = await response.json()
    pendingEditathons.value = data.editathons || []
  } catch (error) {
    console.error('Error fetching pending editathons:', error)
    pendingEditathons.value = []
  } finally {
    loading.value = false
  }
}

function approveEditathon(id) {
  if (confirm('Approve this editathon?')) {
    approveOrReject(id, 'approve')
  }
}

function rejectEditathon(id) {
  const reason = prompt('Enter rejection reason:')
  if (reason !== null) {
    approveOrReject(id, 'reject', reason)
  }
}

async function approveOrReject(id, action, reason = null) {
  try {
    const endpoint = action === 'approve' 
      ? `/api/editathon/${id}/approve`
      : `/api/editathon/${id}/reject`
    
    const options = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reason ? { reason } : {})
    }
    
    const response = await fetch(endpoint, options)
    const data = await response.json()
    
    if (data.success) {
      alert(`✅ Editathon ${action}d successfully!`)
      pendingEditathons.value = pendingEditathons.value.filter(e => e.id !== id)
    } else {
      alert(`❌ Error: ${data.error}`)
    }
  } catch (error) {
    console.error('Error:', error)
    alert(`❌ Failed to ${action} editathon`)
  }
}

function viewDetails(id) {
  router.push(`/editathon/${id}/edit`)
}

onMounted(() => {
  fetchPendingEditathons()
})
</script>

<style scoped>
.approval-queue {
  width: 100%;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.queue-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.9rem;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  background: #f9fafb;
  border-radius: 8px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h4 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #6b7280;
  margin: 0;
}

/* Queue List */
.queue-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.queue-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.queue-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.item-info h4 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.5rem 0;
}

.description {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0 0 0.75rem 0;
}

.meta-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.meta-tag {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #6b7280;
}

.status-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #fef3c7;
  color: #92400e;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
}

/* Item Details */
.item-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  padding: 1rem 0;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  background: #f9fafb;
  margin-bottom: 1rem;
}

.detail-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-group .label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #9ca3af;
  text-transform: uppercase;
}

.detail-group .value {
  font-size: 0.95rem;
  color: #374151;
  font-weight: 500;
}

/* Item Actions */
.item-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.item-actions button {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-approve {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
}

.btn-approve:hover {
  background: #a7f3d0;
}

.btn-reject {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.btn-reject:hover {
  background: #fecaca;
}

.btn-view {
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #93c5fd;
}

.btn-view:hover {
  background: #bfdbfe;
}
</style>