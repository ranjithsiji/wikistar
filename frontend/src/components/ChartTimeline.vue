<template>
  <div class="chart-card">
    <div class="chart-header">
      <div>
        <h3>Editathon Timeline</h3>
        <p>Duration and scheduling of all editathons</p>
      </div>
      <span v-if="!loading && editathons.length > 0" class="count-badge">{{ editathons.length }} events</span>
    </div>
    
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading timeline...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <p>{{ error }}</p>
    </div>
    
    <div v-else-if="editathons.length === 0" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
      <p>No editathons found</p>
    </div>
    
    <canvas v-else ref="chartCanvas"></canvas>
    
    <div v-if="!loading && editathons.length > 0" class="chart-legend">
      <div class="legend-item">
        <span class="legend-dot ongoing"></span>
        <span>Ongoing/Upcoming</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot finished"></span>
        <span>Finished</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Chart from 'chart.js/auto'
import 'chartjs-adapter-date-fns'
import { fetchEditathons } from '../services/api'

const chartCanvas = ref(null)
const editathons = ref([])
const loading = ref(true)
const error = ref(null)
let chart = null

const loadData = async () => {
  try {
    loading.value = true
    error.value = null
    const data = await fetchEditathons()
    editathons.value = data || []
    
    if (chartCanvas.value && editathons.value.length > 0) {
      renderChart()
    }
  } catch (err) {
    error.value = 'Failed to load editathon data'
    console.error('ChartTimeline error:', err)
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartCanvas.value || editathons.value.length === 0) return
  
  if (chart) {
    chart.destroy()
  }
  
  const now = new Date().getTime()
  const labels = editathons.value.map(e => e.name || 'Unnamed')
  const dataPoints = editathons.value.map(e => {
    const start = new Date(e.startDate).getTime()
    const end = new Date(e.endDate).getTime()
    return { x: [start, end], y: e.name || 'Unnamed' }
  })
  
  const backgroundColor = editathons.value.map(e => {
    const endDate = new Date(e.endDate).getTime()
    const startDate = new Date(e.startDate).getTime()
    // Ongoing: start date passed but end date hasn't
    // Upcoming: start date hasn't passed yet
    // Finished: end date passed
    if (endDate > now) {
      return startDate <= now ? '#16a34a' : '#3b82f6' // Green for ongoing, blue for upcoming
    }
    return '#9ca3af' // Grey for finished
  })
  
  chart = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Duration',
        data: dataPoints,
        backgroundColor: backgroundColor,
        borderRadius: 4,
        borderSkipped: false,
        barThickness: 'flex',
        maxBarThickness: 30
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      parsing: { xAxisKey: 'x', yAxisKey: 'y' },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'month',
            displayFormats: {
              month: 'MMM yyyy'
            }
          },
          grid: {
            color: '#e5e7eb',
            drawBorder: false
          },
          ticks: {
            color: '#6b7280',
            font: {
              size: 11
            }
          }
        },
        y: {
          ticks: {
            autoSkip: false,
            color: '#374151',
            font: {
              size: 12
            },
            callback: function(value) {
              const label = this.getLabelForValue(value)
              return label.length > 30 ? label.substring(0, 30) + '...' : label
            }
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
          padding: 12,
          displayColors: false,
          callbacks: {
            title: (context) => {
              const idx = context[0].dataIndex
              return editathons.value[idx]?.name || 'Unnamed'
            },
            label: (context) => {
              const idx = context.dataIndex
              const event = editathons.value[idx]
              if (!event) return ''
              
              const start = new Date(event.startDate).toLocaleDateString()
              const end = new Date(event.endDate).toLocaleDateString()
              const duration = Math.ceil((new Date(event.endDate) - new Date(event.startDate)) / (1000 * 60 * 60 * 24))
              
              return [
                `Start: ${start}`,
                `End: ${end}`,
                `Duration: ${duration} days`,
                event.article_count ? `Articles: ${event.article_count}` : ''
              ].filter(Boolean)
            }
          }
        }
      }
    }
  })
}

onMounted(() => {
  loadData()
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
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 280px;
}

.chart-card canvas {
  width: 100%;
  min-height: 200px;
  max-height: 350px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.chart-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #111827;
  font-weight: 600;
}

.chart-header p {
  margin: 0.15rem 0 0;
  color: #6b7280;
  font-size: 0.8rem;
}

.count-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  padding: 0.3rem 0.85rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.chart-legend {
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #374151;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-dot.ongoing {
  background: linear-gradient(135deg, #16a34a, #22c55e);
}

.legend-dot.finished {
  background: #9ca3af;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 1rem;
  color: #6b7280;
  flex: 1;
}

.loading-state p,
.error-state p,
.empty-state p {
  margin: 0;
  font-size: 0.9rem;
}

.error-state {
  color: #dc2626;
}

.error-state svg {
  color: #dc2626;
}

.empty-state svg {
  width: 32px;
  height: 32px;
  color: #9ca3af;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .chart-card {
    padding: 1rem;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .chart-legend {
    justify-content: center;
  }
}
</style>
