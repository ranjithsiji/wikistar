<template>
  <div class="main-timeline-container my-5">
    <!-- Header -->
    <div class="row mb-5">
      <div class="col-12 text-center">
        <h2 class="display-5 fw-bold mb-3">Editathon Timeline</h2>
        <div class="d-flex justify-content-center gap-2 flex-wrap">
          <div class="input-group input-group-sm" style="max-width: 300px;">
            <span class="input-group-text bg-white border-end-0">🔍</span>
            <input v-model="searchQuery" type="text" class="form-control border-start-0" placeholder="Search...">
          </div>
          <div class="btn-group btn-group-sm shadow-sm">
            <button v-for="s in ['all', 'active', 'upcoming', 'past']" :key="s" 
              @click="filterStatus = s" class="btn btn-outline-primary text-capitalize"
              :class="{ active: filterStatus === s }">{{ s }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Timeline Wrapper -->
    <div class="timeline" ref="timelineWrapper">
      <div v-if="groupedEvents.length === 0" class="text-center py-5">
        <div class="display-1 text-muted">📭</div>
        <p class="lead">No events found matching your criteria.</p>
      </div>

      <div v-for="(group, gIdx) in groupedEvents" :key="group.period" class="timeline-year-group">
        <div class="timeline-year-label mx-auto text-center mb-4">
          <span class="badge bg-dark rounded-pill px-4 py-2 fs-5">{{ group.year }}</span>
        </div>

        <div v-for="(event, eIdx) in group.events" :key="event.id" class="timeline-item" :class="eIdx % 2 === 0 ? 'left' : 'right'">
          <div class="timeline-content card shadow-sm border-0">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge rounded-pill" :style="{ backgroundColor: getWikiColor(event.wiki) }">{{ event.wiki }}</span>
                <small class="text-muted fw-bold">{{ getDayRange(event) }}</small>
              </div>
              <h4 class="card-title fw-bold mb-2">{{ event.title }}</h4>
              <p class="card-text text-secondary mb-3">{{ event.description }}</p>
              <div class="d-flex justify-content-between align-items-center">
                <div class="tags">
                  <span v-for="tag in event.tags" :key="tag" class="badge bg-light text-dark border me-1">#{{ tag }}</span>
                </div>
                <div v-if="isEventActive(event)" class="badge bg-success">
                  <span class="spinner-grow spinner-grow-sm me-1" role="status"></span> Active
                </div>
              </div>
            </div>
          </div>
          <div class="timeline-dot" :style="{ backgroundColor: getWikiColor(event.wiki) }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const rawEvents = ref([])
const filterStatus = ref('all')
const searchQuery = ref('')
const selectedLang = ref('all')

const groupedEvents = computed(() => {
  let filtered = rawEvents.value.filter(event => {
    if (filterStatus.value !== 'all' && getEventStatus(event) !== filterStatus.value) return false
    if (!matchesSearch(event)) return false
    return true
  })

  // Sort by date desc
  filtered.sort((a, b) => new Date(b.start) - new Date(a.start))

  const groups = {}
  filtered.forEach(event => {
    const year = new Date(event.start).getFullYear()
    if (!groups[year]) groups[year] = { year, period: year, events: [] }
    groups[year].events.push(event)
  })

  return Object.values(groups).sort((a, b) => b.year - a.year)
})

const getEventStatus = (event) => {
  const start = new Date(event.start)
  const end = new Date(event.end)
  const now = new Date()
  if (now >= start && now <= end) return 'active'
  if (start > now) return 'upcoming'
  return 'past'
}

const matchesSearch = (event) => {
  const term = searchQuery.value.toLowerCase()
  return (event.title + event.description + event.wiki).toLowerCase().includes(term)
}

const isEventActive = (event) => getEventStatus(event) === 'active'

const getDayRange = (event) => {
  const options = { day: 'numeric', month: 'short' }
  return `${new Date(event.start).toLocaleDateString('en-US', options)} - ${new Date(event.end).toLocaleDateString('en-US', options)}`
}

const getWikiColor = (wiki) => {
  const colors = { 'Wikipedia': '#0d6efd', 'Wikidata': '#dc3545', 'Commons': '#198754', 'Meta': '#6c757d' }
  return colors[wiki] || '#6610f2'
}

const extractTags = (description, name) => {
  const tags = []
  const text = (name + description).toLowerCase()
  if (text.includes('women')) tags.push('Women')
  if (text.includes('asia')) tags.push('Asia')
  if (text.includes('culture')) tags.push('Culture')
  if (tags.length === 0) tags.push('Editathon')
  return tags
}

const fetchEditathons = async () => {
  try {
    const response = await fetch('/api/editathons')
    const data = await response.json()
    rawEvents.value = data.map(e => ({
      id: e.id,
      title: e.name,
      wiki: e.project || 'Wikipedia',
      start: e.startDate || e.start_date,
      end: e.endDate || e.end_date,
      description: e.description,
      tags: extractTags(e.description, e.name)
    }))
  } catch (err) { console.error(err) }
}

onMounted(fetchEditathons)
</script>

<style scoped>
.main-timeline-container {
  max-width: 1000px;
  margin: 0 auto;
}

.timeline {
  position: relative;
  padding: 40px 0;
}

/* Vertical Spine */
.timeline::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #e9ecef;
  transform: translateX(-50%);
  border-radius: 2px;
}

.timeline-item {
  position: relative;
  margin-bottom: 60px;
  width: 50%;
  display: flex;
}

.timeline-item.left {
  left: 0;
  padding-right: 50px;
  justify-content: flex-end;
}

.timeline-item.right {
  left: 50%;
  padding-left: 50px;
  justify-content: flex-start;
}

.timeline-dot {
  position: absolute;
  top: 20px;
  width: 24px;
  height: 24px;
  background: #000;
  border: 4px solid #fff;
  border-radius: 50%;
  z-index: 2;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.left .timeline-dot {
  right: -12px;
}

.right .timeline-dot {
  left: -12px;
}

/* Horizontal line pointing to content */
.timeline-item::after {
  content: '';
  position: absolute;
  top: 31px;
  height: 2px;
  background: #e9ecef;
  width: 30px;
  z-index: 1;
}

.left::after {
  right: 12px;
}

.right::after {
  left: 12px;
}

.timeline-content {
  width: 100%;
  max-width: 420px;
  transition: transform 0.3s ease;
}

.timeline-content:hover {
  transform: translateY(-5px);
}

.timeline-year-label {
  position: relative;
  z-index: 3;
}

@media (max-width: 768px) {
  .timeline::before {
    left: 20px;
  }
  .timeline-item {
    width: 100%;
    left: 0 !important;
    padding-left: 50px !important;
    padding-right: 0 !important;
    justify-content: flex-start !important;
  }
  .timeline-dot {
    left: 8px !important;
  }
  .timeline-item::after {
    left: 20px !important;
  }
  .timeline-content {
    max-width: 100%;
  }
}
</style>
