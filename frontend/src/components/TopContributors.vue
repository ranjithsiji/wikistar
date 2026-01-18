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
  background: linear-gradient(145deg, #ffffff 0%, #f7f9ff 100%);
  border: 1px solid #e4e9f2;
  border-radius: 14px;
  padding: 1.4rem;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
}

.contributors-header {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #f0f0f0;
}

.title-block {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4f46e5, #22c55e);
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 1.1rem;
  box-shadow: 0 8px 18px rgba(79, 70, 229, 0.35);
}

.contributors-header h2 {
  margin: 0;
  font-size: 1.1rem;
  color: #0f172a;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.no-data {
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #999;
  padding: 1.5rem;
  font-size: 0.9rem;
}

.contributors-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.contributor-card {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.9rem 1rem;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e8e8e8;
  transition: all 0.2s ease;
}

.contributor-card:hover {
  background: #f8fafc;
  border-color: #dce2f0;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
}

.rank-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.2);
}

.rank-badge.rank-2 {
  background: #c0c0c0;
}

.rank-badge.rank-3 {
  background: #cd7f32;
}

.contributor-card.rank-1 {
  background: linear-gradient(135deg, #fff8e1, #fffaf0);
  border-color: #fcd34d;
}

.contributor-card.rank-1 .rank-badge {
  background: #ffc107;
  color: #333;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
}

.contributor-card.rank-2 {
  background: #f0f0f0;
}

.contributor-card.rank-3 {
  background: #f7f1e9;
}

.contributor-info {
  flex: 1;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: #e5e7eb;
  display: grid;
  place-items: center;
  font-weight: 700;
  color: #111827;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
}

.avatar.rank-1 { background: #ffe08a; color: #6b4d00; }
.avatar.rank-2 { background: #e5e7eb; color: #4b5563; }
.avatar.rank-3 { background: #f4d7b5; color: #7c4a1d; }

.contributor-name {
  display: block;
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin-bottom: 0.25rem;
  transition: color 0.2s;
  font-size: 0.9rem;
}

.contributor-name:hover {
  color: #5568d3;
  text-decoration: underline;
}

.contributor-stats {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: #666;
}

.stat {
  white-space: nowrap;
}

.stat-separator {
  opacity: 0.4;
  color: #999;
}

.points-display {
  font-weight: 700;
  font-size: 1rem;
  color: #667eea;
  min-width: 45px;
  text-align: right;
  letter-spacing: 0.3px;
}

.contributor-card.rank-1 .points-display {
  color: #ffc107;
  font-size: 1.1rem;
}
</style>
