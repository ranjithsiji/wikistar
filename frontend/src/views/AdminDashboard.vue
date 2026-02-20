<template>
  <div class="admin-dashboard bg-light min-vh-100">
    <!-- Page Header -->
    <div class="page-header bg-white border-bottom">
      <div class="container-xl">
        <div class="d-flex align-items-center justify-content-between py-3">
          <div class="d-flex align-items-center gap-3">
            <div class="avatar-lg bg-danger">A</div>
            <div>
              <h1 class="page-title mb-0">Admin Center</h1>
              <div class="d-flex align-items-center gap-2 mt-1">
                <span class="badge bg-danger">Master Control Panel</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="container-xl py-4">
      <div v-if="!isTrueAdmin" class="alert alert-danger text-center py-5">
        <div style="font-size:3rem; margin-bottom:1rem;">🚫</div>
        <h3>Access Restricted</h3>
        <p>You need administrator privileges to view this section.</p>
        <button class="btn btn-primary mt-3" @click="$router.push('/')">Return Home</button>
      </div>
      <div v-else class="row g-4">
        
        <!-- Sidebar Navigation -->
        <div class="col-lg-3">
          <div class="card shadow-sm border-0 rounded-3 overflow-hidden sticky-top" style="top: 80px;">
            <div class="card-body p-0">
              <nav class="admin-nav">
                <button
                  v-for="tab in tabs"
                  :key="tab.id"
                  class="admin-nav-item"
                  :class="{ active: activeTab === tab.id }"
                  @click="activeTab = tab.id"
                >
                  <i :class="`bi ${tab.icon} me-2`"></i>
                  {{ tab.label }}
                </button>
              </nav>
            </div>
          </div>
        </div>

        <!-- Dynamic Content Area -->
        <div class="col-lg-9">
          <div class="card shadow-sm border-0 rounded-3">
            <div class="card-body p-4">
              <transition name="fade" mode="out-in">

                <!-- Overview -->
                <div v-if="activeTab === 'overview'" key="overview">
                  <h3 class="mb-4">System Overview</h3>
                  <div class="row g-4 mb-4">
                    <div class="col-md-6 col-lg-3">
                      <div class="p-3 bg-primary bg-opacity-10 rounded text-center border">
                        <h2 class="text-primary mb-0">{{ stats?.total_users || 0 }}</h2>
                        <div class="text-muted small text-uppercase">Total Users</div>
                      </div>
                    </div>
                    <div class="col-md-6 col-lg-3">
                      <div class="p-3 bg-success bg-opacity-10 rounded text-center border">
                        <h2 class="text-success mb-0">{{ stats?.total_campaigns || 0 }}</h2>
                        <div class="text-muted small text-uppercase">Campaigns</div>
                      </div>
                    </div>
                    <div class="col-md-6 col-lg-3">
                      <div class="p-3 bg-info bg-opacity-10 rounded text-center border">
                        <h2 class="text-info mb-0">{{ stats?.total_articles || 0 }}</h2>
                        <div class="text-muted small text-uppercase">Articles</div>
                      </div>
                    </div>
                    <div class="col-md-6 col-lg-3">
                      <div class="p-3 bg-warning bg-opacity-10 rounded text-center border">
                        <h2 class="text-warning mb-0">{{ stats?.pending_campaigns || 0 }}</h2>
                        <div class="text-muted small text-uppercase">Pending</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Campaigns -->
                <div v-else-if="activeTab === 'campaigns'" key="campaigns">
                  <div class="d-flex justify-content-between align-items-center mb-3">
                    <h3 class="mb-0">All Campaigns</h3>
                    <div class="d-flex gap-2 flex-wrap">
                      <button
                        v-for="f in statusFilters" :key="f.value"
                        class="btn btn-sm"
                        :class="campaignFilter === f.value ? 'btn-dark' : 'btn-outline-secondary'"
                        @click="campaignFilter = f.value"
                      >{{ f.label }} <span class="badge bg-light text-dark ms-1">{{ getCampaignCount(f.value) }}</span></button>
                    </div>
                  </div>

                  <div class="table-responsive">
                    <table class="table table-hover align-middle">
                      <thead class="table-light">
                        <tr>
                          <th>ID</th>
                          <th>Name</th>
                          <th>Creator</th>
                          <th>Language</th>
                          <th>Dates</th>
                          <th>Status</th>
                          <th>📝</th>
                          <th>👥</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        <template v-for="c in filteredCampaigns" :key="c.id">
                          <!-- Normal row -->
                          <tr v-if="editingCampaignId !== c.id">
                            <td class="text-muted small">{{ c.id }}</td>
                            <td>
                              <router-link :to="`/editathon/${c.id}`" class="fw-bold text-decoration-none">{{ c.name }}</router-link>
                              <div class="text-muted small">{{ c.code }}</div>
                            </td>
                            <td>{{ c.created_by }}</td>
                            <td><span class="badge bg-secondary">{{ c.language || '—' }}</span></td>
                            <td class="small text-muted">
                              <div>{{ formatDate(c.start_date) }}</div>
                              <div>→ {{ formatDate(c.end_date) }}</div>
                            </td>
                            <td>
                              <span class="badge" :class="statusBadge(c.effective_status)">{{ c.effective_status }}</span>
                            </td>
                            <td>{{ c.article_count }}</td>
                            <td>{{ c.jury_count }}</td>
                            <td>
                              <div class="d-flex gap-1 flex-wrap">
                                <button class="btn btn-xs btn-outline-primary" @click="startEdit(c)" title="Edit settings">✏️</button>
                                <button v-if="c.status === 'draft'" class="btn btn-xs btn-outline-success" @click="approveCampaign(c)" title="Approve">✓</button>
                                <button v-if="c.status === 'draft'" class="btn btn-xs btn-outline-warning" @click="rejectCampaign(c)" title="Reject">✕</button>
                                <router-link :to="`/editathon/${c.id}/edit`" class="btn btn-xs btn-outline-secondary" title="Full Edit">⚙️</router-link>
                                <button class="btn btn-xs btn-outline-danger" @click="deleteCampaign(c)" title="Delete">🗑</button>
                              </div>
                            </td>
                          </tr>

                          <!-- Inline edit row -->
                          <tr v-else class="table-warning">
                            <td class="text-muted small">{{ c.id }}</td>
                            <td colspan="2">
                              <input v-model="editForm.name" class="form-control form-control-sm mb-1" placeholder="Campaign Name" />
                              <textarea v-model="editForm.description" class="form-control form-control-sm" placeholder="Description" rows="2" />
                            </td>
                            <td>
                              <input v-model="editForm.language" class="form-control form-control-sm" placeholder="en" style="width:70px" />
                            </td>
                            <td>
                              <input v-model="editForm.start_date" type="date" class="form-control form-control-sm mb-1" />
                              <input v-model="editForm.end_date" type="date" class="form-control form-control-sm" />
                            </td>
                            <td>
                              <select v-model="editForm.status" class="form-select form-select-sm">
                                <option value="draft">draft</option>
                                <option value="active">active</option>
                                <option value="completed">completed</option>
                                <option value="archived">archived</option>
                                <option value="rejected">rejected</option>
                              </select>
                            </td>
                            <td colspan="3">
                              <div class="d-flex gap-2">
                                <button class="btn btn-sm btn-success" @click="saveEdit(c)">💾 Save</button>
                                <button class="btn btn-sm btn-secondary" @click="editingCampaignId = null">Cancel</button>
                              </div>
                            </td>
                          </tr>
                        </template>
                        <tr v-if="filteredCampaigns.length === 0">
                          <td colspan="9" class="text-center text-muted py-4">No campaigns match this filter.</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- Articles -->
                <div v-else-if="activeTab === 'articles'" key="articles">
                  <h3 class="mb-4">Global Article Management</h3>
                  <div class="table-responsive">
                    <table class="table table-hover">
                      <thead>
                        <tr>
                          <th>ID</th><th>Title</th><th>Campaign</th><th>Submitted By</th><th>Status</th><th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="article in articles" :key="article.id">
                          <td>{{ article.id }}</td>
                          <td class="fw-bold">{{ article.title }}</td>
                          <td>
                            <router-link :to="`/editathon/${article.editathon_id}`" class="text-decoration-none">{{ article.editathon_name }}</router-link>
                          </td>
                          <td>{{ article.submitted_by }}</td>
                          <td><span class="badge" :class="article.status === 'accepted' ? 'bg-success' : article.status === 'rejected' ? 'bg-danger' : 'bg-warning text-dark'">{{ article.status }}</span></td>
                          <td><button class="btn btn-sm btn-outline-danger" @click="deleteArticle(article)">Delete</button></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- Users -->
                <div v-else-if="activeTab === 'users'" key="users">
                  <UserManagement />
                </div>

                <!-- Approval Queue -->
                <div v-else-if="activeTab === 'approval'" key="approval">
                  <ApprovalQueue />
                </div>

                <!-- Logs -->
                <div v-else-if="activeTab === 'logs'" key="logs">
                  <h3 class="mb-4">System Audit Logs</h3>
                  <div class="table-responsive" style="max-height: 520px; overflow-y: auto;">
                    <table class="table table-striped table-sm text-sm border">
                      <thead class="table-dark" style="position: sticky; top: 0; z-index: 10;">
                        <tr>
                          <th>Time</th><th>User</th><th>Action</th><th>Entity Type</th><th>Entity ID</th><th>Info</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="log in logs" :key="log.id">
                          <td>{{ new Date(log.created_at).toLocaleString() }}</td>
                          <td><span class="badge bg-secondary">{{ log.username }}</span></td>
                          <td class="fw-bold">{{ log.action }}</td>
                          <td>{{ log.entity_type }}</td>
                          <td>{{ log.entity_id }}</td>
                          <td class="text-muted" style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ JSON.stringify(log.details) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- User Wiki Lookup -->
                <div v-else-if="activeTab === 'user-lookup'" key="user-lookup">
                  <UserLookupPanel />
                </div>

              </transition>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { store } from '../store'
import UserManagement from '../components/PersonalCabinet/UserManagement.vue'
import ApprovalQueue from '../components/PersonalCabinet/ApprovalQueue.vue'
import UserLookupPanel from './UserLookup.vue'

const activeTab = ref('overview')
const stats = ref(null)
const articles = ref([])
const logs = ref([])
const campaigns = ref([])
const campaignFilter = ref('all')
const editingCampaignId = ref(null)
const editForm = ref({})

const isTrueAdmin = computed(() => store.user && store.user.role === 'admin')

const tabs = [
  { id: 'overview', label: 'Overview', icon: 'bi-grid' },
  { id: 'campaigns', label: 'All Campaigns', icon: 'bi-megaphone' },
  { id: 'approval', label: 'Approval Queue', icon: 'bi-inbox' },
  { id: 'articles', label: 'All Articles', icon: 'bi-file-text' },
  { id: 'users', label: 'User Management', icon: 'bi-people' },
  { id: 'user-lookup', label: 'User Lookup', icon: 'bi-search' },
  { id: 'logs', label: 'Audit Logs', icon: 'bi-shield-exclamation' }
]

const statusFilters = [
  { value: 'all', label: 'All' },
  { value: 'running', label: '🟢 Running' },
  { value: 'upcoming', label: '🔵 Upcoming' },
  { value: 'draft', label: '🟡 Draft' },
  { value: 'completed', label: '⚫ Completed' },
  { value: 'rejected', label: '🔴 Rejected' },
  { value: 'archived', label: '🔘 Archived' },
]

const filteredCampaigns = computed(() => {
  if (campaignFilter.value === 'all') return campaigns.value
  return campaigns.value.filter(c => c.effective_status === campaignFilter.value)
})

function getCampaignCount(filterVal) {
  if (filterVal === 'all') return campaigns.value.length
  return campaigns.value.filter(c => c.effective_status === filterVal).length
}

function statusBadge(status) {
  const map = {
    running: 'bg-success', upcoming: 'bg-info text-dark', draft: 'bg-warning text-dark',
    completed: 'bg-secondary', rejected: 'bg-danger', archived: 'bg-dark', active: 'bg-success'
  }
  return map[status] || 'bg-secondary'
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString()
}

function startEdit(c) {
  editingCampaignId.value = c.id
  editForm.value = {
    name: c.name,
    description: c.description,
    language: c.language,
    start_date: c.start_date,
    end_date: c.end_date,
    status: c.status
  }
}

async function saveEdit(c) {
  try {
    const res = await axios.patch(`/api/admin/campaigns/${c.id}`, editForm.value)
    if (res.data.success) {
      // Refresh campaigns
      campaigns.value = campaigns.value.map(x => x.id === c.id ? { ...x, ...editForm.value } : x)
      editingCampaignId.value = null
      alert('Campaign updated successfully')
    }
  } catch (err) {
    alert('Error saving campaign: ' + (err.response?.data?.error || err.message))
  }
}

async function approveCampaign(c) {
  if (!confirm(`Approve "${c.name}"?`)) return
  try {
    const res = await axios.post(`/api/editathon/${c.id}/approve`)
    if (res.data.success) {
      campaigns.value = campaigns.value.map(x => x.id === c.id ? { ...x, status: 'active', effective_status: 'active' } : x)
      alert('Campaign approved and set to active!')
    }
  } catch (err) { alert('Error: ' + (err.response?.data?.error || err.message)) }
}

async function rejectCampaign(c) {
  const reason = prompt(`Rejection reason for "${c.name}":`)
  if (reason === null) return
  try {
    const res = await axios.post(`/api/editathon/${c.id}/reject`, { reason })
    if (res.data.success) {
      campaigns.value = campaigns.value.map(x => x.id === c.id ? { ...x, status: 'rejected', effective_status: 'rejected' } : x)
    }
  } catch (err) { alert('Error: ' + (err.response?.data?.error || err.message)) }
}

async function deleteCampaign(c) {
  if (!confirm(`⚠️ Permanently delete campaign "${c.name}" and ALL its articles/jury data? This cannot be undone!`)) return
  try {
    const res = await axios.delete(`/api/admin/campaigns/${c.id}`)
    if (res.data.success) {
      campaigns.value = campaigns.value.filter(x => x.id !== c.id)
      alert('Campaign deleted permanently.')
      fetchDataForTab('overview')
    }
  } catch (err) { alert('Error: ' + (err.response?.data?.error || err.message)) }
}

async function fetchDataForTab(tab) {
  if (!isTrueAdmin.value) return
  try {
    if (tab === 'overview' || !stats.value) {
      const res = await axios.get('/api/admin/stats')
      stats.value = res.data
    }
    if (tab === 'campaigns') {
      const res = await axios.get('/api/admin/campaigns')
      campaigns.value = res.data
    } else if (tab === 'articles') {
      const res = await axios.get('/api/admin/articles')
      articles.value = res.data
    } else if (tab === 'logs') {
      const res = await axios.get('/api/admin/logs?limit=100')
      logs.value = res.data.logs
    }
  } catch (error) {
    console.error(`Failed loading data for tab ${tab}:`, error)
  }
}

async function deleteArticle(article) {
  if (!confirm(`Delete article #${article.id} (${article.title})?`)) return
  try {
    const res = await axios.delete(`/api/admin/articles/${article.id}`)
    if (res.data.success) {
      articles.value = articles.value.filter(a => a.id !== article.id)
      fetchDataForTab('overview')
    }
  } catch (err) { alert('Error deleting article') }
}

watch(activeTab, (newTab) => fetchDataForTab(newTab))
onMounted(() => fetchDataForTab(activeTab.value))
</script>

<style scoped>
.page-header { box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
.page-title { font-size: 1.3rem; font-weight: 700; color: #1a1a2e; }

.avatar-lg {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 1.4rem; font-weight: 800; flex-shrink: 0;
}

.admin-nav { display: flex; flex-direction: column; }

.admin-nav-item {
  display: flex; align-items: center; padding: 0.9rem 1.2rem;
  border: none; background: transparent; text-align: left;
  font-size: 0.9rem; font-weight: 500; color: #495057;
  cursor: pointer; transition: all 0.15s ease;
  border-left: 3px solid transparent; width: 100%;
}
.admin-nav-item:hover { background: #f8f9fa; color: #dc3545; }
.admin-nav-item.active { background: #ffebe9; color: #dc3545; border-left-color: #dc3545; font-weight: 600; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.text-sm { font-size: 0.85rem; }

.btn-xs {
  padding: 0.2rem 0.45rem;
  font-size: 0.78rem;
  border-radius: 4px;
  line-height: 1.3;
}

@media (max-width: 991px) {
  .admin-nav { flex-direction: row; overflow-x: auto; }
  .admin-nav-item { white-space: nowrap; border-left: none; border-bottom: 3px solid transparent; padding: 0.75rem 1rem; }
  .admin-nav-item.active { border-left: none; border-bottom-color: #dc3545; }
}
</style>
