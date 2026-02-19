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

// Role check using store
const isAdmin = computed(() => {
  return store.user && (store.user.role === 'admin' || store.user.role === 'jury')
})

// NEW: Fetch personal cabinet data from backend
async function fetchPersonalCabinetData() {
  try {
    loading.value = true
    
    if (store.user) {
      currentUser.value = store.user.username
    } else {
      loading.value = false
      return
    }

    const response = await fetch(`http://localhost:5000/api/personal-cabinet/${currentUser.value}`)
    if (!response.ok) throw new Error('Failed to fetch data')
    userData.value = await response.json()
  } catch (error) {
    console.error('Error fetching personal cabinet data:', error)
    // Fallback to mock data if API fails
    userData.value = {
      username: currentUser.value || 'Guest',
      stats: { participated: 3, created: 2, articles: 15, points: 25 },
      participated_editathons: [],
      created_editathons: [],
      articles: []
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPersonalCabinetData()
})
</script>

<template>
  <div class="personal-cabinet">
    <!-- Header -->
    <div class="cabinet-header">
      <div class="header-content">
        <div class="header-left">
          <div class="user-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          </div>
          <div class="header-text">
            <h1>Personal Cabinet</h1>
            <p>{{ currentUser }}'s Account</p>
          </div>
        </div>
        <button @click="$router.back()" class="btn-back">← Back</button>
      </div>
    </div>

    <!-- Show loading state -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading your data...</p>
    </div>

    <!-- Show content when data is loaded -->
    <div v-else class="cabinet-layout">
      <!-- Sidebar Navigation -->
      <aside class="sidebar">
        <nav class="sidebar-nav">
          <button
            class="nav-item"
            :class="{ active: activeTab === 'participated' }"
            @click="activeTab = 'participated'"
          >
            Participation
          </button>
          <button
            class="nav-item"
            :class="{ active: activeTab === 'evaluation' }"
            @click="activeTab = 'evaluation'"
          >
            Evaluation
          </button>
          <button
            class="nav-item"
            :class="{ active: activeTab === 'created' }"
            @click="activeTab = 'created'"
          >
            Created
          </button>
          <button
            v-if="isAdmin"
            class="nav-item"
            :class="{ active: activeTab === 'approval' }"
            @click="activeTab = 'approval'"
          >
            Approval
          </button>
        </nav>
      </aside>

      <!-- Main Content Area -->
      <main class="main-content">
        <transition name="fade" mode="out-in">
          <div :key="activeTab" class="content-pane">
            <!-- Participated Editathons Tab -->
            <ParticipatedEditathons v-if="activeTab === 'participated'" :user="currentUser" :editathons="userData.participated_editathons" />

            <!-- Evaluation (My Articles) Tab -->
            <MyArticles v-if="activeTab === 'evaluation'" :user="currentUser" :articles="userData.articles" />

            <!-- Created Editathons Tab -->
            <CreatedEditathons v-if="activeTab === 'created'" :user="currentUser" :editathons="userData.created_editathons" />

            <!-- Approval Queue Tab (Admin Only) -->
            <div v-if="activeTab === 'approval'">
              <ApprovalQueue v-if="isAdmin" />
              <div v-else class="alert-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; margin-right: 8px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                Admin access required to view approval queue
              </div>
            </div>
          </div>
        </transition>
      </main>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.personal-cabinet {
  min-height: 100vh;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
}

/* Header Section */
.cabinet-header {
  background: white;
  border-bottom: 2px solid #e5e7eb;
  padding: 0.75rem 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-icon {
  width: 48px;
  height: 48px;
  background: #667eea;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-text h1 {
  font-size: 1.2rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.header-text p {
  color: #6b7280;
  font-size: 0.8rem;
  margin: 0.25rem 0 0;
}

.btn-back {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  color: #374151;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
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

/* Layout Container */
.cabinet-layout {
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
  width: 100%;
  gap: 1rem;
  flex: 1;
}

/* Sidebar */
.sidebar {
  width: 250px;
  flex-shrink: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border: 1px solid #e5e7eb;
}

.nav-item {
  text-align: left;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  font-size: 0.95rem;
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 4px solid transparent;
}

.nav-item:hover {
  background: #f9fafb;
  color: #111827;
}

.nav-item.active {
  background: #eff6ff;
  color: #2563eb;
  border-left-color: #2563eb;
  font-weight: 600;
}

/* Main Content */
.main-content {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 1rem;
  min-height: 500px;
}

.content-pane {
  height: 100%;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Alert Box */
.alert-box {
  padding: 1.5rem;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  color: #92400e;
  font-weight: 600;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .cabinet-layout {
    flex-direction: column;
    padding: 1rem;
  }
  
  .sidebar {
    width: 100%;
  }
  
  .sidebar-nav {
    flex-direction: row;
    overflow-x: auto;
  }
  
  .nav-item {
    padding: 0.75rem 1rem;
    white-space: nowrap;
    border-left: none;
    border-bottom: 3px solid transparent;
  }
  
  .nav-item.active {
    border-left: none;
    border-bottom-color: #2563eb;
  }
}
</style>
