<template>
  <div class="chart-card">
    <div class="chart-header">
      <div>
        <h3>📊 Editathon Statistics</h3>
        <p>Progress overview and timeline</p>
      </div>
      <span class="status-badge" :class="statusClass">{{ status }}</span>
    </div>
    <canvas ref="chartCanvas"></canvas>
    <div class="chart-footer">
      <div class="footer-stats">
        <div class="footer-item">
          <strong>{{ stats.articles }}</strong>
          <span>Total Articles</span>
        </div>
        <div class="footer-divider"></div>
        <div class="footer-item">
          <strong>{{ stats.marks }}</strong>
          <span>Reviewed</span>
        </div>
        <div class="footer-divider"></div>
        <div class="footer-item">
          <strong>{{ reviewProgress }}%</strong>
          <span>Completion</span>
        </div>
        <div class="footer-divider"></div>
        <div class="footer-item">
          <strong>{{ daysRemaining }}</strong>
          <span>{{ daysRemainingLabel }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({
      users: 0,
      articles: 0,
      marks: 0,
      withoutMarks: 0
    })
  },
  editathon: {
    type: Object,
    default: () => ({
      name: '',
      startDate: null,
      endDate: null
    })
  }
})

const chartCanvas = ref(null)
let chart = null

const reviewProgress = computed(() => {
  if (props.stats.articles === 0) return 0
  return Math.round((props.stats.marks / props.stats.articles) * 100)
})

const status = computed(() => {
  const startDate = props.editathon.startDate || props.editathon.start_date
  const endDate = props.editathon.endDate || props.editathon.end_date
  
  if (!startDate || !endDate) return 'Unknown'
  const now = new Date()
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  if (now < start) return 'Upcoming'
  if (now > end) return 'Ended'
  return 'Active'
})

const statusClass = computed(() => {
  return status.value.toLowerCase()
})

const daysRemaining = computed(() => {
  const endDate = props.editathon.endDate || props.editathon.end_date
  if (!endDate) return 'N/A'
  
  const now = new Date()
  const end = new Date(endDate)
  const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24))
  
  if (diff < 0) return Math.abs(diff)
  return diff
})

const daysRemainingLabel = computed(() => {
  const endDate = props.editathon.endDate || props.editathon.end_date
  if (!endDate) return 'days'
  
  const now = new Date()
  const end = new Date(endDate)
  const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24))
  
  if (diff < 0) return 'days ago'
  return diff === 1 ? 'day left' : 'days left'
})

const renderChart = () => {
  if (!chartCanvas.value) return

  if (chart) {
    chart.destroy()
  }

  const data = {
    users: props.stats.users || 0,
    articles: props.stats.articles || 0,
    reviewed: props.stats.marks || 0,
    pending: props.stats.withoutMarks || 0
  }

  chart = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Reviewed', 'Pending Reviews'],
      datasets: [
        {
          label: 'Review Status',
          data: [data.reviewed, data.pending],
          backgroundColor: [
            'rgba(34, 197, 94, 0.85)', // Green for reviewed
            'rgba(251, 191, 36, 0.85)'  // Amber for pending
          ],
          borderColor: [
            'rgba(34, 197, 94, 1)',
            'rgba(251, 191, 36, 1)'
          ],
          borderWidth: 2,
          hoverBackgroundColor: [
            'rgba(34, 197, 94, 0.95)',
            'rgba(251, 191, 36, 0.95)'
          ]
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            boxWidth: 12,
            boxHeight: 12,
            padding: 12,
            font: {
              size: 11,
              weight: '500'
            },
            color: '#374151',
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          backgroundColor: '#1f2937',
          titleColor: '#fff',
          bodyColor: '#e5e7eb',
          borderColor: '#374151',
          borderWidth: 1,
          padding: 10,
          displayColors: true,
          titleFont: {
            size: 12,
            weight: 'bold'
          },
          bodyFont: {
            size: 11
          },
          callbacks: {
            label: (context) => {
              const label = context.label || ''
              const value = context.parsed || 0
              const total = props.stats.articles || 0
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
              return `${label}: ${value} articles (${percentage}%)`
            }
          }
        }
      }
    }
  })
}

watch(
  () => [props.stats, props.editathon],
  () => {
    renderChart()
  },
  { deep: true }
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
  min-height: 160px;
  max-height: 200px;
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

.status-badge {
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.status-badge.active {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #ffffff;
}

.status-badge.upcoming {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
}

.status-badge.ended {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: #ffffff;
}

.status-badge.unknown {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  color: #ffffff;
}

.chart-footer {
  padding: 0.6rem;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.footer-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 0.5rem;
}

.footer-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  flex: 1;
}

.footer-item strong {
  font-size: 0.95rem;
  font-weight: 700;
  color: #111827;
}

.footer-item span {
  font-size: 0.7rem;
  color: #6b7280;
  text-align: center;
}

.footer-divider {
  width: 1px;
  height: 30px;
  background: #d1d5db;
}

@media (max-width: 768px) {
  .chart-card {
    padding: 0.6rem;
  }
  
  .footer-stats {
    flex-wrap: wrap;
  }
  
  .footer-divider {
    display: none;
  }
}
</style>
