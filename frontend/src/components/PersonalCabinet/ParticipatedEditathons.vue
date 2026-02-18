<template>
  <div class="participated-section">
    <h2 class="section-title">Editathons You Participate In</h2>

    <div v-if="editathons.length === 0" class="empty-state">
      <p>You haven't participated in any editathons yet.</p>
    </div>

    <div v-else class="editathons-list">
      <article v-for="editathon in editathons" :key="editathon.id" class="editathon-card">
        <div class="card-header">
          <div>
            <router-link :to="`/editathon/${editathon.id}`" class="title-link">
              {{ editathon.name }}
            </router-link>
            <p class="meta-text">
              {{ statusText(editathon.end_date) }} ·
              {{ (editathon.language || 'en').toUpperCase() }} ·
              {{ editathon.project || 'Wikimedia Project' }}
            </p>
          </div>
          <div v-if="editathon.user_summary.rank" class="rank-chip">
            <span class="rank-label">Your rank</span>
            <strong>#{{ editathon.user_summary.rank }}</strong>
            <span class="rank-points">{{ formatPoints(editathon.user_summary.points) }} pts</span>
          </div>
        </div>

        <div class="scoreboard" v-if="editathon.scoreboard?.length">
          <div
            v-for="row in editathon.scoreboard"
            :key="row.username"
            class="score-row"
            :class="{ highlight: row.username === user }"
          >
            <span class="rank">{{ row.rank }}</span>
            <span class="participant">{{ row.username }}</span>
            <span class="points">Σ {{ formatPoints(row.points) }}</span>
          </div>
        </div>
        <div v-else class="empty-scoreboard">
          No scoreboard data yet for this editathon.
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  user: String,
  editathons: {
    type: Array,
    default: () => []
  }
})

function formatPoints(value) {
  if (!value) return '0'
  const num = Number(value)
  return Number.isInteger(num) ? num : num.toFixed(2)
}

function statusText(endDate) {
  if (!endDate) return 'Status unknown'
  const end = new Date(endDate)
  const now = new Date()
  const diffMs = now - end
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return `Ends in ${Math.abs(diffDays)} day${Math.abs(diffDays) === 1 ? '' : 's'}`
  }

  if (diffDays < 30) {
    return `Ended ${diffDays} day${diffDays === 1 ? '' : 's'} ago`
  }

  const months = Math.floor(diffDays / 30)
  if (months < 12) {
    return `Ended ${months} month${months === 1 ? '' : 's'} ago`
  }

  const years = Math.floor(months / 12)
  return `Ended ${years} year${years === 1 ? '' : 's'} ago`
}
</script>

<style scoped>
.participated-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.empty-state,
.empty-scoreboard {
  padding: 1.5rem;
  text-align: center;
  background: #f9fafb;
  border: 1px dashed #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
}

.editathons-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.editathon-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.title-link {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  text-decoration: none;
}

.title-link:hover {
  text-decoration: underline;
}

.meta-text {
  margin: 0.1rem 0 0;
  color: #6b7280;
  font-size: 0.8rem;
}

.rank-chip {
  background: #eef2ff;
  border-radius: 10px;
  padding: 0.5rem 0.75rem;
  text-align: right;
  min-width: 110px;
}

.rank-label {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
}

.rank-chip strong {
  font-size: 1.1rem;
  color: #4338ca;
}

.rank-points {
  display: block;
  font-size: 0.8rem;
  color: #4b5563;
}

.scoreboard {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.score-row {
  display: grid;
  grid-template-columns: 50px 1fr 80px;
  align-items: center;
  padding: 0.5rem 0.75rem;
  font-weight: 500;
  border-bottom: 1px solid #f3f4f6;
}

.score-row:last-child {
  border-bottom: none;
}

.score-row.highlight {
  background: #e0f2fe;
}

.rank {
  font-weight: 600;
  color: #2563eb;
}

.participant {
  color: #111827;
}

.points {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 640px) {
  .score-row {
    grid-template-columns: 30px 1fr 70px;
    font-size: 0.9rem;
  }

  .card-header {
    flex-direction: column;
  }

  .rank-chip {
    align-self: flex-start;
    text-align: left;
  }
}
</style>