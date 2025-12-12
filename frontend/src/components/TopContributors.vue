<template>
  <div class="top-contributors">
    <div class="contributors-header">
      <h2>Top Contributors</h2>
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
</script>

<style scoped>
.top-contributors {
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.contributors-header {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #f0f0f0;
}

.contributors-header h2 {
  margin: 0;
  font-size: 1.05rem;
  color: #1a1a1a;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.no-data {
  text-align: center;
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
  padding: 0.85rem;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
  transition: all 0.2s;
}

.contributor-card:hover {
  background: #f5f7ff;
  border-color: #d0d0d0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
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
  background: #fffbf0;
  border-color: #f0d080;
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
  background: #f5ebe0;
}

.contributor-info {
  flex: 1;
}

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
