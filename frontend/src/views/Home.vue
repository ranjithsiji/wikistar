<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="container-xl">
        <div class="row align-items-center py-5 gy-4">
          <div class="col-lg-6">
            <div class="hero-badge mb-3">
              <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 fs-sm">
                🌍 Wikipedia Edit-a-thon Management
              </span>
            </div>
            <h1 class="hero-title mb-4">
              Coordinate, Review &amp;<br>
              <span class="text-primary">Track Contributions</span>
            </h1>
            <p class="hero-subtitle mb-4">
              WikiSTAR is a unified platform for organizing Wikipedia edit-a-thons,
              managing article reviews, and celebrating contributor achievements.
            </p>
            <div class="d-flex flex-wrap gap-3">
              <router-link to="/create" v-if="store.user" class="btn btn-primary btn-lg px-5">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="me-2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Create Editathon
              </router-link>
              <a href="/api/login" v-else class="btn btn-primary btn-lg px-5">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10,17 15,12 10,7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
                Sign in with Wikimedia
              </a>
              <a href="#editathons" class="btn btn-outline-secondary btn-lg px-5">
                Browse Events
              </a>
            </div>
          </div>
          <div class="col-lg-6 d-none d-lg-flex justify-content-center">
            <div class="hero-graphic">
              <div class="stat-pill pill-1">
                <span class="stat-icon">📝</span>
                <div><div class="stat-val">Active</div><div class="stat-lbl">Editathons</div></div>
              </div>
              <div class="stat-pill pill-2">
                <span class="stat-icon">✅</span>
                <div><div class="stat-val">Reviewed</div><div class="stat-lbl">Articles</div></div>
              </div>
              <div class="stat-pill pill-3">
                <span class="stat-icon">👥</span>
                <div><div class="stat-val">Contributors</div><div class="stat-lbl">Worldwide</div></div>
              </div>
              <div class="wiki-logo-center">W</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Main Content -->
    <div class="container-xl py-5" id="editathons">

      <!-- Ongoing Section -->
      <section class="mb-5">
        <div class="section-header mb-4">
          <div class="d-flex align-items-center gap-3">
            <span class="live-dot"></span>
            <h2 class="section-title mb-0">Live Editathons</h2>
          </div>
          <span class="text-muted small">{{ ongoingEditathons.length }} active</span>
        </div>

        <div v-if="ongoingEditathons.length === 0" class="empty-state">
          <div class="empty-icon">🌱</div>
          <h5>No active editathons right now</h5>
          <p class="text-muted mb-0">Check the timeline below for upcoming events</p>
        </div>

        <div v-else class="row g-4">
          <div class="col-md-6 col-xl-4" v-for="e in ongoingEditathons" :key="e.id">
            <div class="editathon-card">
              <div class="card-top">
                <div class="d-flex align-items-center gap-2 mb-2">
                  <span class="lang-badge">{{ (e.language || 'en').toUpperCase() }}</span>
                  <span class="project-label">{{ e.project || 'Wikipedia' }}</span>
                </div>
                <h5 class="card-title-text">{{ e.name }}</h5>
                <p class="card-desc">{{ e.description }}</p>
              </div>
              <div class="card-bottom">
                <div class="progress-section">
                  <div class="d-flex justify-content-between text-muted small mb-1">
                    <span>Progress</span>
                    <span>Ends {{ formatDate(e.endDate || e.end_date) }}</span>
                  </div>
                  <div class="progress" style="height:5px;border-radius:3px;">
                    <div class="progress-bar bg-success" :style="{ width: calculateProgress(e) + '%' }"></div>
                  </div>
                </div>
                <div class="card-actions">
                  <router-link :to="`/editathon/${e.id}`" class="btn btn-sm btn-outline-secondary">Dashboard</router-link>
                  <router-link v-if="store.user" :to="`/editathon/${e.id}/submit`" class="btn btn-sm btn-primary">Submit Article</router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Timeline Section -->
      <section>
        <div class="section-header mb-4">
          <h2 class="section-title mb-0">All Editathons</h2>
        </div>
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

const ongoingEditathons = computed(() => filteredEditathons.value.filter(isOngoing))

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
.home-page {
  min-height: 100vh;
}

/* Hero */
.hero-section {
  background: linear-gradient(135deg, #f8f9ff 0%, #eef2ff 100%);
  border-bottom: 1px solid #e0e7ff;
}

.hero-title {
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  line-height: 1.15;
  color: #1a1a2e;
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 1.05rem;
  color: #6c757d;
  max-width: 520px;
  line-height: 1.7;
}

/* Hero Graphic */
.hero-graphic {
  position: relative;
  width: 340px;
  height: 300px;
}

.wiki-logo-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90px;
  height: 90px;
  background: linear-gradient(135deg, #0d6efd, #6610f2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2.2rem;
  font-weight: 900;
  box-shadow: 0 10px 40px rgba(13,110,253,0.3);
}

.stat-pill {
  position: absolute;
  background: white;
  border-radius: 14px;
  padding: 0.75rem 1rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 140px;
}

.stat-icon { font-size: 1.5rem; }
.stat-val { font-weight: 700; font-size: 0.85rem; color: #1a1a2e; }
.stat-lbl { font-size: 0.72rem; color: #6c757d; }

.pill-1 { top: 20px; left: 0; animation: float 3s ease-in-out infinite; }
.pill-2 { top: 110px; right: 0; animation: float 3s ease-in-out infinite 1s; }
.pill-3 { bottom: 20px; left: 20px; animation: float 3s ease-in-out infinite 2s; }

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* Section Header */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1a1a2e;
}

.live-dot {
  width: 10px;
  height: 10px;
  background: #198754;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(25,135,84,0.2);
  animation: pulse 1.5s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 2px rgba(25,135,84,0.2); }
  50% { box-shadow: 0 0 0 6px rgba(25,135,84,0.1); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 16px;
  border: 2px dashed #dee2e6;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* Editathon Cards */
.editathon-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: box-shadow 0.25s, transform 0.25s;
}

.editathon-card:hover {
  box-shadow: 0 12px 40px rgba(0,0,0,0.1);
  transform: translateY(-4px);
}

.card-top {
  padding: 1.4rem;
  flex: 1;
}

.card-bottom {
  padding: 1rem 1.4rem 1.4rem;
  border-top: 1px solid #f1f3f5;
}

.lang-badge {
  font-size: 0.7rem;
  font-weight: 700;
  background: #e7f0ff;
  color: #0d6efd;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid #c6dbff;
}

.project-label {
  font-size: 0.78rem;
  color: #6c757d;
  font-weight: 500;
}

.card-title-text {
  font-size: 1rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
  line-height: 1.3;
}

.card-desc {
  font-size: 0.84rem;
  color: #6c757d;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}

.progress-section {
  margin-bottom: 1rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.card-actions .btn {
  border-radius: 8px;
}
</style>
