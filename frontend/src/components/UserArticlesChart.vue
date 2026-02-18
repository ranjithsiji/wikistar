<template>
  <div class="chart-card">
    <div class="chart-header">
      <div>
        <h3>🏆 Top Scorers by Points</h3>
        <p>Highest scoring contributors ranked by total marks</p>
      </div>
      <span class="stats-badge">{{ totalContributors }} total</span>
    </div>
    <canvas ref="chartCanvas"></canvas>
    <div v-if="selectedUser" class="chart-selection">
      <div class="selection-main">
        <span v-if="selectedUser.rank === 1" class="rank-badge gold">🥇 #1</span>
        <span v-else-if="selectedUser.rank === 2" class="rank-badge silver">🥈 #2</span>
        <span v-else-if="selectedUser.rank === 3" class="rank-badge bronze">🥉 #3</span>
        <span v-else class="rank-badge">#{{ selectedUser.rank }}</span>
        <strong>{{ selectedUser.name }}</strong>
      </div>
      <div class="selection-stats">
        <span class="stat-item highlight">{{ formatPoints(selectedUser.points) }} points</span>
        <span class="stat-divider">|</span>
        <span class="stat-item">{{ selectedUser.articles }} article{{ selectedUser.articles !== 1 ? 's' : '' }}</span>
        <span class="stat-divider">|</span>
        <span class="stat-item">Avg: {{ formatPoints(selectedUser.avgPoints) }} pts/article</span>
      </div>
    </div>
    <div v-else class="chart-selection muted">
      👆 Click a bar to see contributor's scoring details
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  leaderboard: {
    type: Array,
    default: () => []
  }
})

const chartCanvas = ref(null)
let chart
const selectedUser = ref(null)

const totalContributors = computed(() => props.leaderboard.length)
const visibleCount = computed(() => Math.min(props.leaderboard.length, 10))

const formatPoints = (points) => {
  if (points === null || points === undefined) return '0.0'
  return Number(points).toFixed(1)
}

const buildDataset = () => {
  const labels = []
  const pointsData = []
  const meta = []
  
  // Sort ONLY by total points - highest marks first!
  const sortedLeaderboard = [...props.leaderboard]
    .sort((a, b) => {
      const aPoints = a.totalPoints ?? 0
      const bPoints = b.totalPoints ?? 0
      return bPoints - aPoints // Highest points first
    })
    .slice(0, 10) // Top 10 only

  sortedLeaderboard.forEach((user, index) => {
    const username = user.username || 'Unknown'
    const displayName = username.length > 15 ? username.substring(0, 15) + '...' : username
    
    // Add rank to label for clarity
    const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`
    labels.push(`${rankEmoji} ${displayName}`)
    
    const totalUserArticles = user.articlesCount ?? user.articles?.length ?? 0
    const totalUserPoints = user.totalPoints ?? 0
    
    pointsData.push(totalUserPoints)
    
    const avgPoints = totalUserArticles > 0 ? totalUserPoints / totalUserArticles : 0
    
    meta.push({
      name: user.username || 'Unknown',
      articles: totalUserArticles,
      points: totalUserPoints,
      avgPoints: avgPoints,
      rank: index + 1
    })
  })

  return { labels, pointsData, meta }
}

const renderChart = () => {
  if (!chartCanvas.value) return
  const { labels, pointsData, meta } = buildDataset()

  if (chart) {
    chart.destroy()
  }

  const maxPoints = Math.max(...pointsData, 1)

  chart = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Total Points',
          data: pointsData,
          backgroundColor: (ctx) => {
            const index = ctx.dataIndex
            // Gold, Silver, Bronze, then gradient red for others
            if (index === 0) return 'rgba(255, 215, 0, 0.9)' // Gold
            if (index === 1) return 'rgba(192, 192, 192, 0.9)' // Silver
            if (index === 2) return 'rgba(205, 127, 50, 0.9)' // Bronze
            
            // Gradient red for the rest based on score
            const value = ctx.parsed?.y ?? 0
            const ratio = maxPoints > 0 ? value / maxPoints : 0
            const intensity = Math.floor(150 + (105 * ratio))
            return `rgba(${intensity}, 50, 50, 0.85)`
          },
          hoverBackgroundColor: (ctx) => {
            const index = ctx.dataIndex
            if (index === 0) return 'rgba(255, 215, 0, 1)'
            if (index === 1) return 'rgba(192, 192, 192, 1)'
            if (index === 2) return 'rgba(205, 127, 50, 1)'
            return 'rgba(220, 38, 38, 0.95)'
          },
          borderRadius: 8,
          borderSkipped: false,
          barThickness: 'flex',
          maxBarThickness: 60
        }
      ]
    },
    options: {
      indexAxis: 'y', // Horizontal bars for better label reading
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Total Points (Marks)',
            color: '#111827',
            font: {
              size: 11,
              weight: 'bold'
            }
          },
          ticks: {
            color: '#6b7280',
            font: {
              size: 10
            },
            precision: 1,
            callback: function(value) {
              return Number(value).toFixed(1)
            }
          },
          grid: {
            color: 'rgba(229, 231, 235, 0.5)',
            drawBorder: false
          }
        },
        y: {
          ticks: {
            color: '#374151',
            font: {
              size: 10,
              weight: '600'
            },
            autoSkip: false
          },
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: '#1f2937',
          titleColor: '#fff',
          bodyColor: '#e5e7eb',
          borderColor: '#374151',
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          titleFont: {
            size: 12,
            weight: 'bold'
          },
          bodyFont: {
            size: 11
          },
          callbacks: {
            title: (context) => {
              const data = meta[context[0].dataIndex]
              let rankText = `#${data.rank}`
              if (data.rank === 1) rankText = '🥇 #1 TOP SCORER'
              else if (data.rank === 2) rankText = '🥈 #2'
              else if (data.rank === 3) rankText = '🥉 #3'
              return `${rankText} - ${data.name}`
            },
            label: (context) => {
              const data = meta[context.dataIndex]
              return [
                `Total Points: ${formatPoints(data.points)}`,
                `Articles Submitted: ${data.articles}`,
                `Average: ${formatPoints(data.avgPoints)} points/article`
              ]
            }
          }
        }
      },
      onClick: (_evt, elements) => {
        if (!elements?.length) {
          selectedUser.value = null
          return
        }
        const idx = elements[0].index
        selectedUser.value = meta[idx]
      }
    }
  })
}

watch(
  () => props.leaderboard,
  () => {
    selectedUser.value = null
    renderChart()
  },
  { deep: true, immediate: true }
)

onMounted(() => {
  renderChart()
})

onBeforeUnmount(() => {
  if (chart) {
    chart.destroy()
  }
})
</script>

<style scoped>
.chart-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 0.75rem;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  height: 100%;
  max-height: 350px;
}

.chart-card canvas {
  width: 100%;
  min-height: 220px;
  max-height: 270px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.chart-header h3 {
  margin: 0;
  font-size: 0.95rem;
  color: #111827;
}

.chart-header p {
  margin: 0;
  color: #6b7280;
  font-size: 0.75rem;
}

.stats-badge {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: #ffffff;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25);
}

.chart-selection {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.8rem;
  padding: 0.6rem;
  border-radius: 8px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  color: #111827;
}

.selection-main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rank-badge {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: #ffffff;
  padding: 0.15rem 0.5rem;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 700;
  min-width: 32px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.rank-badge.gold {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #000;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.5);
  font-size: 0.8rem;
  animation: pulse-gold 2s ease-in-out infinite;
}

.rank-badge.silver {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  color: #000;
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.5);
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #cd7f32 0%, #d4914b 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.5);
}

@keyframes pulse-gold {
  0%, 100% {
    box-shadow: 0 2px 8px rgba(255, 215, 0, 0.5);
  }
  50% {
    box-shadow: 0 4px 16px rgba(255, 215, 0, 0.8);
    transform: scale(1.05);
  }
}

.selection-main strong {
  color: #991b1b;
  font-weight: 600;
}

.selection-stats {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  color: #6b7280;
  font-size: 0.75rem;
  padding-left: 1.8rem;
}

.stat-item {
  font-weight: 500;
}

.stat-item.highlight {
  color: #dc2626;
  font-weight: 800;
  font-size: 0.85rem;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  padding: 0.15rem 0.5rem;
  border-radius: 5px;
  border: 1px solid #fecaca;
}

.stat-divider {
  color: #d1d5db;
}

.chart-selection.muted {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  font-style: italic;
  font-size: 0.8rem;
}
</style>
