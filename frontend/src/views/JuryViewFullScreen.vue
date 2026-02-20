<template>
  <div class="jury-view-fullscreen">
    <!-- Header -->
    <div class="jury-header">
      <button class="back-btn" @click="goBack">← Back</button>
      <h1>Jury Management</h1>
      <div class="header-stats">
        <div class="stat-badge">
          <span class="label">Total Jury</span>
          <span class="value">{{ juries.length }}</span>
        </div>
        <div class="stat-badge">
          <span class="label">Active</span>
          <span class="value">{{ juries.length }}</span>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="jury-content">
      <!-- Left: Jury List -->
      <div class="jury-list-panel">
        <div class="panel-header">
          <h2>Jury Members</h2>
          <button class="btn-add" @click="showAddModal = true">+ Add Jury</button>
        </div>

        <div class="jury-list">
          <div 
            v-for="jury in juries" 
            :key="jury.id"
            class="jury-card"
            :class="{ active: selectedJury?.id === jury.id }"
            @click="selectJury(jury)"
          >
            <div class="jury-avatar">{{ jury.username.charAt(0).toUpperCase() }}</div>
            <div class="jury-details">
              <a :href="`https://en.wikipedia.org/wiki/User:${jury.username}`" target="_blank" class="jury-name">
                {{ jury.username }}
              </a>
              <div class="jury-meta">
                <span class="role">Juror</span>
              </div>
            </div>
            <button class="btn-remove" @click.stop="removeJury(jury.id)" title="Remove jury member">×</button>
          </div>
        </div>
      </div>

      <!-- Right: Selected Jury Stats -->
      <div class="jury-stats-panel">
        <div v-if="selectedJury" class="jury-profile">
          <div class="profile-header">
            <div class="profile-avatar">{{ selectedJury.username.charAt(0).toUpperCase() }}</div>
            <div class="profile-info">
              <h2>{{ selectedJury.username }}</h2>
              <p class="role">Jury Member</p>
            </div>
          </div>

          <div class="profile-stats">
            <div class="stat-item">
              <span class="stat-label">Status</span>
              <span class="stat-value status-active">Active</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Added</span>
              <span class="stat-value">{{ formatDate(selectedJury.addedDate) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Reviews</span>
              <span class="stat-value">{{ selectedJury.reviewsCount || 0 }}</span>
            </div>
          </div>

          <div class="profile-actions">
            <a :href="`https://en.wikipedia.org/wiki/User:${selectedJury.username}`" target="_blank" class="btn-action">
              View on Wikipedia
            </a>
            <button class="btn-action danger" @click="removeJury(selectedJury.id)">
              Remove from Jury
            </button>
          </div>
        </div>

        <div v-else class="no-selection">
          <p>Select a jury member to view details</p>
        </div>
      </div>
    </div>

    <!-- Add Jury Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click="showAddModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Add Jury Member</h2>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>Wikipedia Username</label>
            <input
              type="text"
              v-model="newJuryUsername"
              placeholder="Enter Wikipedia username..."
              @keyup.enter="addJury"
            >
            <div v-if="jurySuggestions.length > 0" class="suggestions-list">
              <div
                v-for="user in jurySuggestions"
                :key="user.name"
                class="suggestion-item"
                @click="selectSuggestion(user.name)"
              >
                {{ user.name }}
              </div>
            </div>
          </div>

          <div v-if="addError" class="error-message">{{ addError }}</div>

          <div class="modal-actions">
            <button class="btn btn-primary" @click="addJury">Add Jury Member</button>
            <button class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="jury-footer">
      <button class="btn btn-primary" @click="saveLargeJuries">Save Changes</button>
      <button class="btn btn-secondary" @click="goBack">Close</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { store } from '../store'

const router = useRouter()
const route = useRoute()

const juries = ref([])
const selectedJury = ref(null)
const showAddModal = ref(false)
const newJuryUsername = ref('')
const jurySuggestions = ref([])
const addError = ref('')

onMounted(async () => {
  // Load juries from route params or API
  const editathonId = route.params.editathonId || route.params.id
  if (editathonId) {
    // Fetch jury data from API
    try {
      const response = await fetch(`/api/editathon/${editathonId}`)
      const data = await response.json()
      juries.value = data.juries || []
      
      // Check if current user is a jury member
      const isJury = store.user && juries.value.some(jury => jury.username === store.user.username)
      if (!isJury) {
        alert('Access denied: Only jury members can manage jury settings')
        router.push(`/editathon/${editathonId}`)
        return
      }
    } catch (error) {
      console.error('Error loading jury data:', error)
      loadMockJuries()
    }
  }
})

function loadMockJuries() {
  juries.value = [
    { id: 1, username: 'Admin1', addedDate: '2025-12-01', reviewsCount: 5 },
    { id: 2, username: 'Reviewer2', addedDate: '2025-12-02', reviewsCount: 3 },
    { id: 3, username: 'Judge3', addedDate: '2025-12-03', reviewsCount: 7 }
  ]
}

function selectJury(jury) {
  selectedJury.value = jury
}

async function addJury() {
  const username = newJuryUsername.value.trim()
  
  if (!username) {
    addError.value = 'Please enter a username'
    return
  }

  // Check if already exists
  if (juries.value.some(j => j.username === username)) {
    addError.value = 'This user is already a jury member'
    return
  }

  // Add new jury
  juries.value.push({
    id: Math.max(...juries.value.map(j => j.id), 0) + 1,
    username: username,
    addedDate: new Date().toISOString().split('T')[0],
    reviewsCount: 0
  })

  newJuryUsername.value = ''
  addError.value = ''
  showAddModal.value = false
}

function selectSuggestion(username) {
  newJuryUsername.value = username
  jurySuggestions.value = []
}

function removeJury(id) {
  juries.value = juries.value.filter(j => j.id !== id)
  if (selectedJury.value?.id === id) {
    selectedJury.value = null
  }
}

function saveLargeJuries() {
  // Save jury data to API
  console.log('Saving juries:', juries.value)
  // TODO: Call API to save
}

function goBack() {
  router.back()
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.jury-view-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.jury-header {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 1.5rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.back-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0;
  margin-right: 1rem;
  transition: color 0.2s;
}

.back-btn:hover {
  color: #5568d3;
}

.jury-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #1a1a1a;
  flex: 1;
}

.header-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
}

.stat-badge .label {
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.stat-badge .value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
}

.jury-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  padding: 2rem;
  overflow: hidden;
}

.jury-list-panel,
.jury-stats-panel {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.1rem;
  color: #1a1a1a;
}

.btn-add {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  transition: background 0.2s;
}

.btn-add:hover {
  background: #5568d3;
}

.jury-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.jury-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem;
  margin-bottom: 0.5rem;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.jury-card:hover {
  background: #f0f4ff;
  border-color: #d0d0d0;
}

.jury-card.active {
  background: #f0f4ff;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.jury-avatar {
  width: 32px;
  height: 32px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.jury-details {
  flex: 1;
  min-width: 0;
}

.jury-name {
  display: block;
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.jury-name:hover {
  text-decoration: underline;
}

.jury-meta {
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.2rem;
}

.role {
  display: inline-block;
  background: #f0f0f0;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-weight: 600;
}

.btn-remove {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 1.5rem;
  padding: 0;
  line-height: 1;
  transition: color 0.2s;
  flex-shrink: 0;
}

.btn-remove:hover {
  color: #d32f2f;
}

.jury-stats-panel {
  padding: 1.5rem;
}

.jury-profile {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.profile-avatar {
  width: 48px;
  height: 48px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.profile-info h2 {
  margin: 0;
  font-size: 1.1rem;
  color: #1a1a1a;
}

.profile-info .role {
  color: #666;
  font-size: 0.85rem;
}

.profile-stats {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.stat-label {
  font-weight: 600;
  color: #666;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stat-value {
  font-weight: 700;
  color: #1a1a1a;
  font-size: 0.9rem;
}

.status-active {
  color: #2e7d32;
}

.profile-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn-action {
  padding: 0.75rem 1rem;
  border: 1px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  text-decoration: none;
  display: block;
  text-align: center;
  transition: all 0.2s;
}

.btn-action:hover {
  background: #667eea;
  color: white;
}

.btn-action.danger {
  border-color: #d32f2f;
  color: #d32f2f;
}

.btn-action.danger:hover {
  background: #d32f2f;
  color: white;
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  text-align: center;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 400px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.1rem;
  color: #1a1a1a;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #999;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 0.7rem;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d0d0d0;
  border-top: none;
  border-radius: 0 0 6px 6px;
  max-height: 150px;
  overflow-y: auto;
  z-index: 10;
  margin-top: -1px;
}

.suggestion-item {
  padding: 0.7rem;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f5f5f5;
  font-size: 0.9rem;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: #f0f4ff;
}

.error-message {
  background: #fef2f2;
  color: #d32f2f;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  border-left: 3px solid #d32f2f;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5568d3;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.jury-footer {
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 1rem 2rem;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.jury-footer .btn {
  padding: 0.75rem 1.5rem;
}

@media (max-width: 1024px) {
  .jury-content {
    grid-template-columns: 1fr;
  }
}
</style>
