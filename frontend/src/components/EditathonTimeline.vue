<template>
  <div class="timeline-container">
    <!-- Header -->
    <div class="timeline-header">
      <div class="header-content">
        <div class="header-left">
          <div class="icon-box">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
          </div>
          <h2 class="timeline-title">Editathon Timeline</h2>
        </div>

        <div class="header-controls">
          <div class="search-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
            <input
              v-model="searchQuery"
              type="text"
              class="search-input"
              placeholder="Search editathons"
            />
          </div>

          <!-- Filter Buttons -->
          <div class="filter-buttons">
            <button 
              v-for="status in ['all', 'active', 'upcoming', 'past']"
              :key="status"
              @click="filterStatus = status"
              class="filter-btn"
              :class="{ active: filterStatus === status }">
              {{ status === 'all' ? 'All Events' : status }}
            </button>
          </div>

          <!-- Language Filter -->
          <div class="select-wrapper">
            <select v-model="selectedLang" class="lang-select">
              <option value="all">All Projects</option>
              <option
                v-for="wiki in availableLanguages"
                :key="wiki"
                :value="wiki"
              >
                {{ wiki }}
              </option>
            </select>
          </div>

          <!-- Sort Button -->
          <button @click="toggleSort" class="sort-btn" :title="sortOrder === 'desc' ? 'Newest First' : 'Oldest First'">
            <svg v-if="sortOrder === 'desc'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/><path d="m21 16-4 4-4-4"/><path d="M17 20V4"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Timeline Content -->
    <div class="timeline-content">
      <div class="timeline-stats">
        Showing <strong>{{ displayedEventsCount }}</strong> of <strong>{{ filteredEventsCount }}</strong> events
      </div>

      <div class="timeline-wrapper" ref="timelineWrapper" @scroll="handleScroll">
        <!-- Timeline Spine -->
        <div class="timeline-spine"></div>

        <!-- Empty State -->
        <div v-if="groupedEvents.length === 0" class="empty-state">
          <div class="empty-card">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
            <h3>No events found</h3>
            <p>There are no {{ filterStatus }} events matching your filters.</p>
          </div>
        </div>

        <!-- Timeline Groups -->
        <transition-group name="fade">
          <div v-for="(group, index) in displayedGroups" :key="group.period" class="timeline-group">
            <!-- Month Header -->
            <div class="month-header">
              <div class="month-date">
                <span class="month-name">{{ group.monthName }}</span>
                <span class="month-year">{{ group.year }}</span>
              </div>
            </div>

            <!-- Events List -->
            <div class="events-list">
              <div v-for="event in group.events" :key="event.id" class="event-row">
                <!-- Left Column: Date & Status -->
                <div class="event-left">
                  <!-- Colored Indicator -->
                  <div class="event-indicator" :class="getWikiColorClass(event.wiki)"></div>

                  <div class="event-date">
                    <div class="date-range">{{ getDayRange(event) }}</div>
                    <div class="date-duration">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                      {{ event.durationLabel }}
                    </div>
                    <div v-if="isEventActive(event)" class="active-badge">ACTIVE NOW</div>
                  </div>
                </div>

                <!-- Right Column: Event Card -->
                <div class="event-right">
                  <div class="event-card">
                    <div class="card-accent" :class="getEventStatusColor(event)"></div>
                    <div class="card-content">
                      <div class="card-header">
                        <h3 class="card-title">{{ event.title }}</h3>
                        <span class="card-wiki">{{ event.wiki }}</span>
                      </div>
                      <p class="card-description">{{ event.description }}</p>
                      <div class="card-tags">
                        <span v-for="tag in event.tags" :key="tag" class="tag">#{{ tag }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition-group>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const DEFAULT_PROJECTS = [
  'Wikipedia',
  'Wikivoyage',
  'Wiktionary',
  'Wikibooks',
  'Wikinews',
  'Wikisource',
  'Wikiquote',
  'Wikiversity',
  'Wikidata',
  'Wikimedia'
]

const rawEvents = ref([])
const itemsToShow = ref(999)
const timelineWrapper = ref(null)

const selectedLang = ref('all')
const sortOrder = ref('desc')
const filterStatus = ref('all')
const searchQuery = ref('')

const mockToday = new Date()

const availableLanguages = computed(() => {
  const langs = new Set(DEFAULT_PROJECTS)
  rawEvents.value.forEach(event => {
    if (event.wiki) {
      langs.add(event.wiki)
    }
  })
  return Array.from(langs).sort()
})

const getEventStatus = (event) => {
  const start = new Date(event.start)
  const end = new Date(event.end)
  const today = new Date(mockToday)
  today.setHours(0, 0, 0, 0)
  start.setHours(0, 0, 0, 0)
  end.setHours(23, 59, 59, 999)

  if (today >= start && today <= end) return 'active'
  if (start > today) return 'upcoming'
  return 'past'
}

const matchesSearch = (event) => {
  const term = searchQuery.value.trim().toLowerCase()
  if (!term) return true

  const haystacks = [
    event.title || '',
    event.description || '',
    event.wiki || '',
    (event.tags || []).join(' ')
  ]

  return haystacks.some(value => value.toLowerCase().includes(term))
}

const filteredEventsCount = computed(() => {
  let count = 0
  rawEvents.value.forEach(e => {
    if (selectedLang.value !== 'all' && e.wiki !== selectedLang.value) return
    if (filterStatus.value !== 'all' && getEventStatus(e) !== filterStatus.value) return
    if (!matchesSearch(e)) return
    count++
  })
  return count
})

const groupedEvents = computed(() => {
  let filtered = rawEvents.value.filter(event => {
    if (selectedLang.value !== 'all' && event.wiki !== selectedLang.value) return false
    return matchesSearch(event)
  })

  filtered = filtered.filter(event => {
    if (filterStatus.value === 'all') return true
    return getEventStatus(event) === filterStatus.value
  })

  filtered.sort((a, b) => {
    // First priority: active events come first
    const statusA = getEventStatus(a)
    const statusB = getEventStatus(b)
    
    if (statusA === 'active' && statusB !== 'active') return -1
    if (statusA !== 'active' && statusB === 'active') return 1
    
    // Then sort by date
    const dateA = new Date(a.start)
    const dateB = new Date(b.start)
    return sortOrder.value === 'desc' ? dateB - dateA : dateA - dateB
  })

  const groups = {}
  filtered.forEach(event => {
    const date = new Date(event.start)
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`

    if (!groups[key]) {
      groups[key] = {
        period: key,
        year: date.getFullYear(),
        monthName: date.toLocaleDateString('en-US', { month: 'long' }),
        events: []
      }
    }
    groups[key].events.push(event)
  })

  const groupArray = Object.values(groups)
  groupArray.sort((a, b) => {
    return sortOrder.value === 'desc'
      ? b.period.localeCompare(a.period)
      : a.period.localeCompare(b.period)
  })

  return groupArray
})

const displayedGroups = computed(() => {
  let eventCount = 0
  const result = []
  
  for (let group of groupedEvents.value) {
    if (eventCount >= itemsToShow.value) break
    
    const eventsToShow = group.events.slice(0, itemsToShow.value - eventCount)
    result.push({
      ...group,
      events: eventsToShow
    })
    eventCount += eventsToShow.length
  }
  
  return result
})

const displayedEventsCount = computed(() => {
  return displayedGroups.value.reduce((sum, group) => sum + group.events.length, 0)
})

const handleScroll = () => {
  if (!timelineWrapper.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = timelineWrapper.value
  
  // If user scrolls near the bottom, load more items
  if (scrollHeight - scrollTop - clientHeight < 100) {
    itemsToShow.value += 3
  }
}

const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
}

const getDayRange = (event) => {
  const start = new Date(event.start)
  const end = new Date(event.end)
  const startStr = start.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })
  if (event.start === event.end) return startStr
  const endStr = start.getMonth() === end.getMonth()
    ? end.getDate()
    : end.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })
  return `${startStr} - ${endStr}`
}

const isEventActive = (event) => {
  return getEventStatus(event) === 'active'
}

const getEventStatusColor = (event) => {
  const status = getEventStatus(event)
  // Return green for active, grey for finished
  return status === 'active' ? 'color-active' : 'color-finished'
}

const getWikiColorClass = (wiki) => {
  const map = {
    'Global': 'color-indigo',
    'En': 'color-blue',
    'Fr': 'color-purple',
    'De': 'color-yellow',
    'Es': 'color-orange',
    'Commons': 'color-red',
    'Ig': 'color-green',
    'Nrm': 'color-teal',
    'Data': 'color-pink',
    'Source': 'color-cyan',
    'Meta': 'color-gray',
    'Wikipedia': 'color-blue',
    'Wikimedia': 'color-indigo',
    'Wikivoyage': 'color-teal',
    'Wiktionary': 'color-green',
    'Wikibooks': 'color-orange',
    'Wikinews': 'color-yellow',
    'Wikisource': 'color-cyan',
    'Wikiquote': 'color-purple',
    'Wikiversity': 'color-pink',
    'Wikidata': 'color-red'
  }
  return map[wiki] || 'color-gray'
}

const calculateDuration = (start, end) => {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const diffTime = Math.abs(endDate - startDate)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1
  
  if (diffDays === 1) return '1 Day'
  if (diffDays <= 7) return `${diffDays} Days`
  if (diffDays <= 31) return `${Math.ceil(diffDays / 7)} Week${Math.ceil(diffDays / 7) > 1 ? 's' : ''}`
  return `${Math.ceil(diffDays / 30)} Month${Math.ceil(diffDays / 30) > 1 ? 's' : ''}`
}

const extractTags = (description, name) => {
  const tags = []
  const lowerName = name.toLowerCase()
  const lowerDesc = description.toLowerCase()
  
  if (lowerName.includes('women') || lowerName.includes('feminism')) tags.push('Women')
  if (lowerName.includes('asian')) tags.push('Asia')
  if (lowerName.includes('ramadan') || lowerName.includes('folklore')) tags.push('Culture')
  if (lowerName.includes('translation')) tags.push('Translation')
  if (lowerDesc.includes('contest')) tags.push('Contest')
  if (tags.length === 0) tags.push('Editathon')
  
  return tags
}

const fetchEditathons = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/editathons')
    const data = await response.json()
    
    rawEvents.value = data.map(editathon => {
      const start = editathon.startDate ? editathon.startDate.split('T')[0] : new Date().toISOString().split('T')[0]
      const end = editathon.endDate ? editathon.endDate.split('T')[0] : new Date().toISOString().split('T')[0]
      const wikiLabel = editathon.project || 'Wikimedia Project'
      
      return {
        id: editathon.id,
        title: editathon.name,
        wiki: wikiLabel,
        projectDomain: editathon.project_domain || null,
        start: start,
        end: end,
        durationLabel: calculateDuration(start, end),
        description: `${editathon.description} - ${editathon.article_count} articles by ${editathon.user_count} participants`,
        tags: extractTags(editathon.description, editathon.name)
      }
    })
  } catch (error) {
    console.error('Error fetching editathons:', error)
    rawEvents.value = []
  }
}

onMounted(() => {
  fetchEditathons()
})
</script>

<style scoped>
.timeline-container {
  background: #f8fafc;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 2rem;
}

/* Header */
.timeline-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 0.75rem 1rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.icon-box {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.3rem;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-box svg {
  width: 16px;
  height: 16px;
}

.timeline-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-wrapper svg {
  position: absolute;
  left: 0.5rem;
  color: #9ca3af;
  pointer-events: none;
}

.search-input {
  padding: 0.3rem 0.5rem 0.3rem 1.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 500;
  background: #fff;
  min-width: 180px;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.08);
}

.filter-buttons {
  display: flex;
  background: #f3f4f6;
  padding: 0.15rem;
  border-radius: 5px;
  gap: 0.15rem;
}

.filter-btn {
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: capitalize;
}

.filter-btn.active {
  background: white;
  color: #667eea;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.select-wrapper {
  position: relative;
}

.lang-select {
  appearance: none;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  color: #374151;
  padding: 0.3rem 1.5rem 0.3rem 0.6rem;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.lang-select:hover {
  background: #f3f4f6;
}

.lang-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.08);
}

.sort-btn {
  padding: 0.3rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sort-btn svg {
  width: 16px;
  height: 16px;
}

.sort-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

/* Timeline Content */
.timeline-content {
  padding: 0.75rem;
}

.timeline-stats {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: white;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
}

.timeline-wrapper {
  position: relative;
  max-height: 500px;
  overflow-y: auto;
  overflow-x: hidden;
  border-radius: 8px;
}

.timeline-wrapper::-webkit-scrollbar {
  width: 10px;
}

.timeline-wrapper::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.timeline-wrapper::-webkit-scrollbar-thumb {
  background: #667eea;
  border-radius: 4px;
}

.timeline-wrapper::-webkit-scrollbar-thumb:hover {
  background: #5568d3;
}

/* Firefox Scrollbar */
.timeline-wrapper {
  scrollbar-color: #667eea #f1f5f9;
  scrollbar-width: thin;
}

.timeline-spine {
  position: absolute;
  left: 110px;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  z-index: 0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 1.5rem 0;
  margin-left: 125px;
}

.empty-card {
  background: white;
  display: inline-block;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.empty-card svg {
  color: #d1d5db;
  margin-bottom: 0.75rem;
  width: 36px;
  height: 36px;
}

.empty-card h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.375rem;
}

.empty-card p {
  color: #6b7280;
  margin: 0;
  font-size: 0.8rem;
}

/* Timeline Groups */
.timeline-group {
  margin-bottom: 1.5rem;
  position: relative;
  z-index: 1;
}

.month-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}

.month-date {
  width: 110px;
  text-align: right;
  padding-right: 1.25rem;
}

.month-name {
  display: block;
  font-size: 1rem;
  font-weight: 700;
  color: #9ca3af;
  line-height: 1;
}

.month-year {
  display: block;
  font-size: 0.7rem;
  color: #9ca3af;
  font-weight: 600;
}

/* Events List */
.events-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.event-row {
  display: flex;
  position: relative;
}

/* Event Left Column */
.event-left {
  width: 110px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  padding-right: 1.25rem;
  position: relative;
}

.event-indicator {
  position: absolute;
  left: 110px;
  top: 4px;
  width: 4px;
  height: 32px;
  transform: translateX(-50%);
  border-radius: 2px;
  z-index: 1;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.event-indicator:hover {
  transform: translateX(-50%) scale(1.05);
}

.event-date {
  text-align: right;
  width: 100%;
}

.date-range {
  font-weight: 600;
  color: #374151;
  font-size: 0.7rem;
  line-height: 1.3;
}

.date-duration {
  font-size: 0.65rem;
  color: #9ca3af;
  font-weight: 600;
  margin-top: 0.15rem;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.15rem;
}

.date-duration svg {
  width: 10px;
  height: 10px;
}

.active-badge {
  margin-top: 0.3rem;
  display: inline-block;
  padding: 0.15rem 0.3rem;
  border-radius: 2px;
  font-size: 0.55rem;
  font-weight: 700;
  background: #10b981;
  color: white;
  box-shadow: 0 1px 2px rgba(16, 185, 129, 0.2);
}

/* Event Right Column */
.event-right {
  flex: 1;
  padding-left: 1.25rem;
}

.event-card {
  background: white;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: all 0.2s;
}

.event-card:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-accent {
  height: 3px;
  width: 100%;
}

.card-content {
  padding: 0.75rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
  gap: 0.5rem;
}

.card-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
  line-height: 1.3;
  transition: color 0.2s;
}

.event-card:hover .card-title {
  color: #667eea;
}

.card-wiki {
  flex-shrink: 0;
  padding: 0.15rem 0.35rem;
  border-radius: 3px;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.card-description {
  color: #6b7280;
  font-size: 0.7rem;
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.tag {
  font-size: 0.65rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.15rem 0.35rem;
  border-radius: 2px;
  transition: background 0.2s;
}

.tag:hover {
  background: #e5e7eb;
}

/* Color Classes */
.color-indigo { background: #6366f1; }
.color-blue { background: #3b82f6; }
.color-purple { background: #a855f7; }
.color-yellow { background: #eab308; }
.color-orange { background: #f97316; }
.color-red { background: #ef4444; }
.color-green { background: #10b981; }
.color-teal { background: #14b8a6; }
.color-pink { background: #ec4899; }
.color-cyan { background: #06b6d4; }
.color-gray { background: #6b7280; }

/* Status Color Classes */
.color-active { background: #10b981; }
.color-finished { background: #9ca3af; }

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Responsive */
@media (max-width: 768px) {
  .timeline-spine {
    left: 28px;
  }

  .event-left {
    width: auto;
    padding-right: 1rem;
  }

  .event-indicator {
    left: 28px;
    height: 40px;
  }

  .event-right {
    padding-left: 1rem;
  }

  .month-header {
    padding-left: 3rem;
  }

  .month-date {
    width: auto;
    text-align: left;
  }

  .event-date {
    text-align: left;
  }

  .date-duration {
    justify-content: flex-start;
  }

  .empty-state {
    margin-left: 0;
  }

  .filter-buttons {
    order: 2;
    width: 100%;
  }
}
</style>
