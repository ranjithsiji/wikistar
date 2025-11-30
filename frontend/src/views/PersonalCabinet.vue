<script setup>
import { ref, onMounted, computed } from 'vue'
import PersonalDashboard from '../components/PersonalCabinet/PersonalDashboard.vue'
import ParticipatedEditathons from '../components/PersonalCabinet/ParticipatedEditathons.vue'
import CreatedEditathons from '../components/PersonalCabinet/CreatedEditathons.vue'
import ApprovalQueue from '../components/PersonalCabinet/ApprovalQueue.vue'
import MyArticles from '../components/PersonalCabinet/MyArticles.vue'

const activeTab = ref('dashboard')
const currentUser = ref('Clinta') // Replace with actual user from auth
const userData = ref(null)
const loading = ref(true)

// Mock admin check - replace with actual auth
const isAdmin = computed(() => {
  const adminUsers = ['Clinta', 'admin', 'Ranjithjsiji']
  return adminUsers.includes(currentUser.value)
})

// NEW: Fetch personal cabinet data from backend
async function fetchPersonalCabinetData() {
  try {
    loading.value = true
    const response = await fetch(`http://localhost:5000/api/personal-cabinet/${currentUser.value}`)
    if (!response.ok) throw new Error('Failed to fetch data')
    userData.value = await response.json()
  } catch (error) {
    console.error('Error fetching personal cabinet data:', error)
    // Fallback to mock data if API fails
    userData.value = {
      username: currentUser.value,
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
            <p>{{ currentUser }}'s Account Dashboard</p>
          </div>
        </div>
        <button @click="$router.back()" class="btn-back">← Back to Home</button>
      </div>
    </div>

    <!-- Show loading state -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading your data...</p>
    </div>

    <!-- Show content when data is loaded -->
    <div v-else class="cabinet-content">
      <!-- Modern Tab Navigation -->
      <div class="tab-navigation">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'dashboard' }"
          @click="activeTab = 'dashboard'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="12 3 20 7.5 20 16.5 12 21 4 16.5 4 7.5 12 3"></polyline><polyline points="12 12 20 7.5"></polyline><polyline points="12 12 12 21"></polyline><polyline points="12 12 4 7.5"></polyline></svg>
          <span class="tab-label">Dashboard</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'participated' }"
          @click="activeTab = 'participated'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          <span class="tab-label">Participated</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'created' }"
          @click="activeTab = 'created'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          <span class="tab-label">Created</span>
        </button>
        <button
          v-if="isAdmin"
          class="tab-btn"
          :class="{ active: activeTab === 'approval' }"
          @click="activeTab = 'approval'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"></path><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          <span class="tab-label">Approval Queue</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'articles' }"
          @click="activeTab = 'articles'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="13" x2="12" y2="17"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
          <span class="tab-label">Articles</span>
        </button>
      </div>

      <!-- Tab Content with smooth transitions -->
      <div class="tab-content-wrapper">
        <transition name="fade" mode="out-in">
          <div :key="activeTab" class="tab-pane">
            <!-- Dashboard Tab -->
            <PersonalDashboard v-if="activeTab === 'dashboard'" :user="currentUser" :stats="userData.stats" />

            <!-- Participated Editathons Tab -->
            <ParticipatedEditathons v-if="activeTab === 'participated'" :user="currentUser" :editathons="userData.participated_editathons" />

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

            <!-- My Articles Tab -->
            <MyArticles v-if="activeTab === 'articles'" :user="currentUser" :articles="userData.articles" />
          </div>
        </transition>
      </div>
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
}

/* Header Section */
.cabinet-header {
  background: white;
  border-bottom: 2px solid #e5e7eb;
  padding: 2rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
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
  font-size: 1.75rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.25rem;
}

.header-text p {
  color: #6b7280;
  font-size: 0.9rem;
}

.btn-back {
  padding: 0.75rem 1.5rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  color: #374151;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
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

/* Cabinet Content */
.cabinet-content {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

/* Tab Navigation - Modern & Responsive */
.tab-navigation {
  display: flex;
  gap: 0.5rem;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
  flex-wrap: wrap;
  border: 1px solid #e5e7eb;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1.2rem;
  background: transparent;
  border: 2px solid transparent;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.tab-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.2);
}

@media (max-width: 768px) {
  .tab-label {
    display: none;
  }
  
  .tab-btn {
    padding: 0.75rem;
  }
  
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
}

/* Tab Content */
.tab-content-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 2rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tab-pane {
  animation: slideIn 0.3s ease;
}

/* Fade transition for tab content */
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
</style>
