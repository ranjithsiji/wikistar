<template>
  <div class="timeline-v3-container my-5">
    <!-- Clean Header -->
    <div class="row mb-4 align-items-end">
      <div class="col-md-6">
        <h2 class="fw-bold mb-1">Timeline</h2>
        <p class="text-muted small mb-0">Discover and participate in ongoing and upcoming editathons.</p>
      </div>
      <div class="col-md-6 d-flex justify-content-md-end gap-2 mt-3 mt-md-0">
        <div class="input-group input-group-sm w-auto">
          <span class="input-group-text bg-white border-end-0"><i class="bi bi-search">🔍</i></span>
          <input v-model="searchQuery" type="text" class="form-control border-start-0" placeholder="Filter events...">
        </div>
        <div class="dropdown">
          <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
            {{ filterStatus.charAt(0).toUpperCase() + filterStatus.slice(1) }}
          </button>
          <ul class="dropdown-menu dropdown-menu-end">
            <li v-for="s in ['all', 'active', 'upcoming', 'past']" :key="s">
              <a class="dropdown-item" href="#" @click.prevent="filterStatus = s">{{ s.charAt(0).toUpperCase() + s.slice(1) }}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Scrollable Timeline Section -->
    <div class="timeline-scroll-wrapper shadow-sm rounded-3 bg-white">
      <div v-if="groupedEvents.length === 0" class="text-center py-5">
        <div class="display-1 text-muted opacity-25">📭</div>
        <p class="lead text-muted">No events found matching your current filters.</p>
      </div>

      <div class="timeline-body p-4" ref="timelineScrollArea">
        <div v-for="group in groupedEvents" :key="group.year" class="timeline-year-block">
          
          <div v-for="(event, eIdx) in group.events" :key="event.id" class="timeline-row">
            <!-- Left Side: Year (only for first item in group or specific milestones) -->
            <div class="timeline-left">
              <span v-if="eIdx === 0" class="year-label">{{ group.year }}</span>
            </div>

            <!-- Middle: Line & Dot -->
            <div class="timeline-middle">
              <div class="vertical-line"></div>
              <div class="timeline-dot" 
                   :class="{ 'is-active': isEventActive(event) }"
                   :style="{ backgroundColor: isEventActive(event) ? getWikiColor(event.wiki) : '#cbd5e0' }">
                <span v-if="isEventActive(event)" class="dot-pulse" :style="{ backgroundColor: getWikiColor(event.wiki) }"></span>
              </div>
            </div>

            <!-- Right: Content Card -->
            <div class="timeline-right">
              <div class="event-card p-3" :class="{ 'card-active': isEventActive(event) }">
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <h5 class="event-title fw-bold m-0" :style="{ color: isEventActive(event) ? getWikiColor(event.wiki) : '#2d3748' }">
                    {{ event.title }}
                  </h5>
                  <span class="badge rounded-pill fw-normal" 
                        :style="{ backgroundColor: getWikiColor(event.wiki) + '15', color: getWikiColor(event.wiki), border: '1px solid ' + getWikiColor(event.wiki) + '30' }">
                    {{ event.wiki }}
                  </span>
                </div>
                
                <p class="event-desc text-secondary small mb-3">{{ event.description }}</p>
                
                <div class="d-flex justify-content-between align-items-center">
                  <div class="event-meta small text-muted">
                    <span class="me-3"><i class="bi bi-calendar"></i> {{ formatDateRange(event) }}</span>
                    <span v-if="event.article_count"><i class="bi bi-file-text"></i> {{ event.article_count }} articles</span>
                  </div>
                  <div class="event-tags">
                    <span v-for="tag in event.tags" :key="tag" class="tag-pill">#{{ tag }}</span>
                  </div>
                </div>

                <!-- Action Button for Active -->
                <div v-if="isEventActive(event)" class="mt-3">
                  <router-link :to="`/editathon/${event.id}`" class="btn btn-sm btn-primary px-3 rounded-pill fw-bold">
                    Join Editathon
                  </router-link>
                </div>
              </div>
            </div>
          </div>

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
const timelineScrollArea = ref(null)

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
    if (!groups[year]) groups[year] = { year, events: [] }
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

const isEventActive = (event) => getEventStatus(event) === 'active'

const matchesSearch = (event) => {
  const term = searchQuery.value.toLowerCase()
  return (event.title + event.description + event.wiki).toLowerCase().includes(term)
}

const formatDateRange = (event) => {
  const options = { month: 'short', day: 'numeric' }
  const start = new Date(event.start).toLocaleDateString('en-US', options)
  const end = new Date(event.end).toLocaleDateString('en-US', options)
  return `${start} - ${end}`
}

const getWikiColor = (wiki) => {
  const colors = { 'Wikipedia': '#3366cc', 'Wikidata': '#990000', 'Commons': '#00af89', 'Meta': '#006699' }
  return colors[wiki] || '#666'
}

const extractTags = (description, name) => {
  const tags = []
  const text = (name + (description || '')).toLowerCase()
  if (text.includes('women')) tags.push('Women')
  if (text.includes('asia')) tags.push('Asia')
  if (text.includes('culture')) tags.push('Culture')
  if (tags.length === 0) tags.push('Community')
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
      article_count: e.article_count,
      tags: extractTags(e.description, e.name)
    }))
  } catch (err) { console.error(err) }
}

onMounted(fetchEditathons)
</script>

<style scoped>
.timeline-v3-container {
  max-width: 900px;
  margin: 0 auto;
}

.timeline-scroll-wrapper {
  max-height: 700px;
  overflow-y: auto;
  border: 1px solid #edf2f7;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 transparent;
}

.timeline-scroll-wrapper::-webkit-scrollbar {
  width: 6px;
}

.timeline-scroll-wrapper::-webkit-scrollbar-thumb {
  background-color: #cbd5e0;
  border-radius: 10px;
}

.timeline-row {
  display: flex;
  min-height: 100px;
}

/* Left: Year Column */
.timeline-left {
  width: 100px;
  flex-shrink: 0;
  padding-top: 15px;
  text-align: right;
  padding-right: 30px;
}

.year-label {
  font-size: 1.5rem;
  font-weight: 800;
  color: #4a5568;
  letter-spacing: -0.5px;
}

.is-active-year .year-label {
  color: #3182ce;
}

/* Middle: Line Column */
.timeline-middle {
  width: 24px;
  position: relative;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.vertical-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: #edf2f7;
  z-index: 1;
}

.timeline-dot {
  position: relative;
  width: 16px;
  height: 16px;
  background-color: #cbd5e0;
  border-radius: 50%;
  margin-top: 24px;
  z-index: 2;
  border: 4px solid #fff;
  transition: all 0.3s ease;
}

.timeline-dot.is-active {
  width: 20px;
  height: 20px;
  margin-top: 22px;
  box-shadow: 0 0 0 4px rgba(66, 153, 225, 0.1);
}

.dot-pulse {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  animation: pulse-ring 2s infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.5; }
  100% { transform: scale(2.4); opacity: 0; }
}

/* Right: Content Column */
.timeline-right {
  flex-grow: 1;
  padding-bottom: 40px;
  padding-left: 30px;
}

.event-card {
  background-color: #fff;
  border: 1px solid #f0f4f8;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.event-card:hover {
  border-color: #e2e8f0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transform: translateX(4px);
}

.card-active {
  border-left: 4px solid #3182ce;
  background-color: #fafcfe;
}

.event-title {
  font-size: 1.15rem;
  line-height: 1.3;
}

.tag-pill {
  font-size: 0.75rem;
  color: #718096;
  margin-left: 8px;
}

/* Timeline Group Padding */
.timeline-year-block {
  margin-bottom: 20px;
}

@media (max-width: 600px) {
  .timeline-left {
    width: 60px;
    padding-right: 15px;
  }
  .year-label {
    font-size: 1.1rem;
  }
  .timeline-right {
    padding-left: 15px;
  }
}
</style>
