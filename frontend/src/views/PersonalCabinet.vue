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
    <div class="header">
      <h2>👤 Personal Cabinet - {{ currentUser }}</h2>
      <button @click="$router.back()" class="back-btn">← Back to Home</button>
    </div>

    <!-- Show loading state -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading your data...</p>
    </div>

    <!-- Show content when data is loaded -->
    <div v-else>
      <!-- Tabs -->
      <div class="tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'dashboard' }"
          @click="activeTab = 'dashboard'"
        >
          📊 Dashboard
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'participated' }"
          @click="activeTab = 'participated'"
        >
          🏆 Participated Editathons
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'created' }"
          @click="activeTab = 'created'"
        >
          🛠️ Created by You
        </button>
        <button
          v-if="isAdmin"
          class="tab-btn"
          :class="{ active: activeTab === 'approval' }"
          @click="activeTab = 'approval'"
        >
          ⏳ Approval Queue
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'articles' }"
          @click="activeTab = 'articles'"
        >
          📝 My Articles
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Dashboard Tab -->
        <div v-if="activeTab === 'dashboard'">
          <PersonalDashboard :user="currentUser" :stats="userData.stats" />
        </div>

        <!-- Participated Editathons Tab -->
        <div v-if="activeTab === 'participated'">
          <ParticipatedEditathons :user="currentUser" :editathons="userData.participated_editathons" />
        </div>

        <!-- Created Editathons Tab -->
        <div v-if="activeTab === 'created'">
          <CreatedEditathons :user="currentUser" :editathons="userData.created_editathons" />
        </div>

        <!-- Approval Queue Tab (Admin Only) -->
        <div v-if="activeTab === 'approval'">
          <ApprovalQueue v-if="isAdmin" />
          <div v-else class="alert">
            ❌ Admin access required to view approval queue.
          </div>
        </div>

        <!-- My Articles Tab -->
        <div v-if="activeTab === 'articles'">
          <MyArticles :user="currentUser" :articles="userData.articles" />
        </div>
      </div>
    </div>
  </div>
</template>
