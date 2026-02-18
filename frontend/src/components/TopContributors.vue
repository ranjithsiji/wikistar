<template>
    <div class="top-contributors">
      <div class="contributors-header">
        <div class="title-block">
          <div class="title-icon">★</div>
          <div>
            <h2>Top Contributors</h2>
            <p class="subtitle">Leaders by points and articles</p>
          </div>
        </div>
        <div class="badge">Top 5</div>
      </div>

    <div v-if="sortedLeaderboard.length === 0" class="no-data">
      No contributors yet
    </div>

    <div v-else class="contributors-list">
      <div 
        v-for="(contributor, index) in sortedLeaderboard.slice(0, 5)" 
        :key="contributor.id"
        class="contributor-card"
        :class="{ 'rank-1': index === 0, 'rank-2': index === 1, 'rank-3': index === 2 }"
      >
        <div class="rank-badge" :class="`rank-${index + 1}`">
          {{ index + 1 }}
        </div>
          <div class="avatar" :class="`rank-${index + 1}`">{{ getInitials(contributor.username) }}</div>
        
        <div class="contributor-info">
          <a 
            :href="`https://${wikiLanguage}.wikipedia.org/wiki/User:${contributor.username}`"
            target="_blank"
            class="contributor-name"
          >
            {{ contributor.username }}
          </a>
          <div class="contributor-stats">
            <span class="stat">{{ contributor.articlesCount || 0 }} articles</span>
            <span class="stat-separator">•</span>
            <span class="stat">{{ contributor.totalPoints || 0 }} points</span>
          </div>
            <div class="progress">
              <div class="progress-fill" :style="{ width: progressWidth(contributor.totalPoints) }"></div>
            </div>
        </div>

        <div class="points-display">
          {{ contributor.totalPoints || 0 }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  leaderboard: {
    type: Array,
    default: () => []
  },
  wikiLanguage: {
    type: String,
    default: 'en'
  }
})

const sortedLeaderboard = computed(() => {
  if (!props.leaderboard || !Array.isArray(props.leaderboard)) {
    return []
  }
  return [...props.leaderboard].sort((a, b) => (b.totalPoints || 0) - (a.totalPoints || 0))
})

const maxPoints = computed(() => {
  const first = sortedLeaderboard.value[0]
  return first ? (first.totalPoints || 0) : 0
})

function progressWidth(points) {
  const max = maxPoints.value || 1
  const value = Math.max(points || 0, 0)
  return `${Math.min((value / max) * 100, 100)}%`
}

function getInitials(name = '') {
  if (!name) return '?'
  const parts = name.split(/\s+|_/).filter(Boolean)
  const first = parts[0]?.[0] || ''
  const second = parts[1]?.[0] || ''
  return (first + second || first).toUpperCase()
}
</script>

<style scoped>
.top-contributors {
  background: #ffffff;
  border: 1px solid #e0e6f1;
  border-radius: 12px;
  padding: 12px;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
  height: 100%; /* Fill the grid cell */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.top-contributors:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.contributors-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9eef7;
  margin-bottom: 8px;
}

.title-block {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-block .title-icon {
  font-size: 1.1rem;
  color: #f9a825; /* Gold star */
}

.title-block h2 {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.title-block .subtitle {
  display: none; /* Hide for compact view */
}

.badge {
  background-color: #e7f3ff;
  color: #007bff;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 3px 6px;
  border-radius: 6px;
}

.contributors-list {
  overflow-y: auto;
  flex-grow: 1;
  margin: 0 -4px; /* Counteract padding on items */
}

.contributor-card {
  display: flex;
  align-items: center;
  padding: 6px 4px;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: background-color 0.2s ease;
}

.contributor-card:hover {
  background-color: #f8faff;
}

.rank-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: #566573;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.avatar {
  display: none; /* Hide avatar for compact view */
}

.contributor-info {
  flex-grow: 1;
  margin-left: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contributor-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #34495e;
  text-decoration: none;
}
.contributor-name:hover {
  text-decoration: underline;
}

.contributor-stats {
  display: none; /* Hide for compact view */
}

.progress {
  display: none; /* Hide for compact view */
}

.points-display {
  font-size: 0.85rem;
  font-weight: 600;
  color: #007bff;
  padding-left: 8px;
}

/* Special styling for top ranks */
.contributor-card.rank-1 .rank-badge { color: #d4af37; } /* Gold */
.contributor-card.rank-2 .rank-badge { color: #c0c0c0; } /* Silver */
.contributor-card.rank-3 .rank-badge { color: #cd7f32; } /* Bronze */

.no-data {
  text-align: center;
  padding: 20px;
  color: #7f8c8d;
  font-size: 0.9rem;
}
</style>
