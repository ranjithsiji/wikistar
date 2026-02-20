<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import ParticipatedEditathons from '../components/PersonalCabinet/ParticipatedEditathons.vue'
import CreatedEditathons from '../components/PersonalCabinet/CreatedEditathons.vue'
import ApprovalQueue from '../components/PersonalCabinet/ApprovalQueue.vue'
import MyArticles from '../components/PersonalCabinet/MyArticles.vue'
import { store } from '../store'

const activeTab = ref('participated')
const currentUser = ref(null)
const userData = ref(null)
const loading = ref(true)
const error = ref(null)

const isAdmin = computed(() => {
  return store.user && (store.user.role === 'admin' || store.user.role === 'jury')
})

const tabs = computed(() => {
  const base = [
    { id: 'participated', label: 'My Participation', icon: 'bi-trophy' },
    { id: 'evaluation', label: 'My Articles', icon: 'bi-journal-text' },
    { id: 'created', label: 'Created', icon: 'bi-folder-plus' },
  ]
  if (isAdmin.value) {
    base.push({ id: 'approval', label: 'Approval Queue', icon: 'bi-check2-circle' })
  }
  return base
})

async function fetchPersonalCabinetData() {
  try {
    loading.value = true
    error.value = null

    if (store.user) {
      currentUser.value = store.user.username
    } else {
      loading.value = false
      return
    }

    const response = await axios.get(`/api/personal-cabinet/${currentUser.value}`)
    userData.value = response.data
  } catch (err) {
    console.error('Error fetching personal cabinet data:', err)
    error.value = 'Failed to load your data. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPersonalCabinetData()
})
</script>

<template>
  <div class="personal-cabinet bg-light min-vh-100">
    <!-- Page Header -->
    <div class="page-header bg-white border-bottom">
      <div class="container-xl">
        <div class="d-flex align-items-center justify-content-between py-3">
          <div class="d-flex align-items-center gap-3">
            <div class="avatar-lg">
              {{ currentUser ? currentUser.charAt(0).toUpperCase() : '?' }}
            </div>
            <div>
              <h1 class="page-title mb-0">{{ currentUser || 'Personal Cabinet' }}</h1>
              <div class="d-flex align-items-center gap-2 mt-1">
                <span class="badge text-capitalize"
                  :class="store.user?.role === 'admin' ? 'bg-danger' : store.user?.role === 'jury' ? 'bg-warning text-dark' : 'bg-secondary'">
                  {{ store.user?.role || 'participant' }}
                </span>
                <span class="text-muted small">Wikipedia contributor</span>
              </div>
            </div>
          </div>
          <button class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1" @click="$router.back()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
            Back
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="d-flex flex-column align-items-center justify-content-center" style="min-height:60vh;">
      <div class="spinner-border text-primary mb-3" role="status"></div>
      <p class="text-muted">Loading your data...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="container-xl py-5">
      <div class="alert alert-danger d-flex align-items-center gap-2" role="alert">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        {{ error }}
        <button class="btn btn-sm btn-outline-danger ms-auto" @click="fetchPersonalCabinetData">Retry</button>
      </div>
    </div>

    <!-- Not Logged In -->
    <div v-else-if="!store.user" class="container-xl py-5 text-center">
      <div class="py-5">
        <div style="font-size:4rem;margin-bottom:1rem;">🔒</div>
        <h3>Sign in to view your cabinet</h3>
        <p class="text-muted mb-4">Access your editathon history, articles, and contributions</p>
        <a href="/api/login" class="btn btn-primary btn-lg px-5">Sign in with Wikimedia</a>
      </div>
    </div>

    <!-- Main Layout -->
    <div v-else class="container-xl py-4">
      <div class="row g-4">

        <!-- Sidebar (desktop) / Scrollable tabs (mobile) -->
        <div class="col-lg-3">
          <div class="card shadow-sm border-0 rounded-3 overflow-hidden sticky-top" style="top: 80px;">
            <div class="card-body p-0">
              <nav class="cabinet-nav">
                <button
                  v-for="tab in tabs"
                  :key="tab.id"
                  class="cabinet-nav-item"
                  :class="{ active: activeTab === tab.id }"
                  @click="activeTab = tab.id"
                >
                  <i :class="`bi ${tab.icon} me-2`"></i>
                  {{ tab.label }}
                  <span v-if="tab.id === 'approval'" class="badge bg-danger ms-auto small">!</span>
                </button>
              </nav>
            </div>
          </div>
        </div>

        <!-- Content Area -->
        <div class="col-lg-9">
          <div class="card shadow-sm border-0 rounded-3">
            <div class="card-body p-4">
              <transition name="fade" mode="out-in">
                <div :key="activeTab">
                  <ParticipatedEditathons v-if="activeTab === 'participated'" :user="currentUser" :editathons="userData?.participated_editathons || []" />
                  <MyArticles v-if="activeTab === 'evaluation'" :user="currentUser" :articles="userData?.articles || []" />
                  <CreatedEditathons v-if="activeTab === 'created'" :user="currentUser" :editathons="userData?.created_editathons || []" />
                  <ApprovalQueue v-if="activeTab === 'approval' && isAdmin" />
                  <div v-if="activeTab === 'approval' && !isAdmin" class="alert alert-warning">
                    <strong>Access denied.</strong> You need admin or jury privileges to view the approval queue.
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.page-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #1a1a2e;
}

.avatar-lg {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #0d6efd, #6610f2);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.4rem;
  font-weight: 800;
  flex-shrink: 0;
}

/* Sidebar Nav */
.cabinet-nav {
  display: flex;
  flex-direction: column;
}

.cabinet-nav-item {
  display: flex;
  align-items: center;
  padding: 0.9rem 1.2rem;
  border: none;
  background: transparent;
  text-align: left;
  font-size: 0.9rem;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
  transition: all 0.15s ease;
  border-left: 3px solid transparent;
  width: 100%;
}

.cabinet-nav-item:hover {
  background: #f8f9fa;
  color: #0d6efd;
}

.cabinet-nav-item.active {
  background: #eef4ff;
  color: #0d6efd;
  border-left-color: #0d6efd;
  font-weight: 600;
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 991px) {
  .cabinet-nav {
    flex-direction: row;
    overflow-x: auto;
  }
  .cabinet-nav-item {
    white-space: nowrap;
    border-left: none;
    border-bottom: 3px solid transparent;
    padding: 0.75rem 1rem;
  }
  .cabinet-nav-item.active {
    border-left: none;
    border-bottom-color: #0d6efd;
  }
}
</style>
