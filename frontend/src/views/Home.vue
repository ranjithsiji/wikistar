<template>
  <div class="home-page bg-light min-vh-100 pb-5">
    <!-- Hero Section -->
    <section class="hero-section bg-white border-bottom py-5 mb-5">
      <div class="container py-4">
        <div class="row align-items-center">
          <div class="col-lg-8">
            <h1 class="display-4 fw-bold text-dark mb-3">Wiki <span class="text-primary">Edit-a-thons Reviews</span></h1>
            <p class="lead text-secondary mb-4">A unified platform for managing Wikipedia content drives, jury reviews, and contribution tracking.</p>
            <div class="d-flex gap-2">
              <router-link to="/create" v-if="store.user" class="btn btn-primary px-4 py-2 fw-bold">
                🚀 Create New Editathon
              </router-link>
              <a href="/api/login" v-else class="btn btn-primary px-4 py-2 fw-bold">
                Get Started
              </a>
              <a href="#timeline" class="btn btn-outline-secondary px-4 py-2">Explore Timeline</a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="container">
      <!-- Ongoing Editathons Section -->
      <section class="mb-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="fw-bold m-0"><span class="badge bg-success me-2">LIVE</span> Ongoing Editathons</h2>
          <span class="text-muted fw-bold">{{ ongoingEditathons.length }} active matches</span>
        </div>

        <div v-if="ongoingEditathons.length === 0" class="alert alert-light border shadow-sm text-center py-5">
          <div class="mb-3 fs-1">🌱</div>
          <h4>No active editathons at the moment</h4>
          <p class="text-muted">Check the timeline below for upcoming events!</p>
        </div>

        <div class="row g-4">
          <div class="col-md-6 col-lg-4" v-for="e in ongoingEditathons" :key="e.id">
            <div class="card h-100 shadow-sm border-0 transition-hover">
              <div class="card-body p-4">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-1">
                    {{ (e.language || 'en').toUpperCase() }}
                  </span>
                  <small class="text-muted fw-bold">{{ e.project || 'Wikipedia' }}</small>
                </div>
                <h5 class="card-title fw-bold mb-3">{{ e.name }}</h5>
                <p class="card-text text-secondary small mb-4 line-clamp-3">{{ e.description }}</p>
                
                <div class="bg-light rounded p-3 mb-4">
                  <div class="d-flex justify-content-between small text-muted">
                    <span>Ends on</span>
                    <span class="fw-bold text-dark">{{ formatDate(e.endDate || e.end_date) }}</span>
                  </div>
                  <div class="progress mt-2" style="height: 4px;">
                    <div class="progress-bar bg-success" role="progressbar" :style="{ width: calculateProgress(e) + '%' }"></div>
                  </div>
                </div>

                <div class="d-flex gap-2 mt-auto">
                  <router-link :to="`/editathon/${e.id}`" class="btn btn-dark btn-sm flex-grow-1">Dashboard</router-link>
                  <router-link :to="`/editathon/${e.id}/submit`" class="btn btn-primary btn-sm px-3">Submit</router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Main Timeline Section -->
      <section id="timeline">
        <EditathonTimeline />
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchEditathons } from '../services/api'
import EditathonTimeline from '../components/EditathonTimeline.vue'
import { store } from '../store'

const editathons = ref([])

const filteredEditathons = computed(() => {
  if (!store.selectedLanguage) return editathons.value
  return editathons.value.filter(e => e.language === store.selectedLanguage)
})

const parseDate = (value) => {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

const isOngoing = (editathon) => {
  const now = new Date()
  const start = parseDate(editathon.startDate || editathon.start_date)
  const end = parseDate(editathon.endDate || editathon.end_date)

  if (editathon.status === 'active') return true
  if (editathon.status === 'completed' || editathon.status === 'archived') return false

  return start && end && start <= now && end >= now
}

const ongoingEditathons = computed(() => {
  return filteredEditathons.value.filter(isOngoing)
})

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const calculateProgress = (e) => {
  const start = parseDate(e.startDate || e.start_date)
  const end = parseDate(e.endDate || e.end_date)
  const now = new Date()
  if (!start || !end) return 0
  const total = end - start
  const current = now - start
  return Math.min(100, Math.max(0, (current / total) * 100))
}

onMounted(async () => {
  editathons.value = await fetchEditathons()
})
</script>

<style scoped>
.transition-hover {
  transition: all 0.3s ease;
}

.transition-hover:hover {
  transform: translateY(-8px);
  box-shadow: 0 1rem 3rem rgba(0,0,0,.175) !important;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}

.hero-section {
  background: linear-gradient(135deg, #ffffff 0%, #f1f4f9 100%);
}

.badge-outline-primary {
  background: transparent;
  border: 1px solid #0d6efd;
  color: #0d6efd;
}
</style>
