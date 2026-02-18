<template>
  <div class="chart-card">
    <div class="chart-header">
      <div>
        <h3>Articles by Editathon</h3>
        <p>Article submissions across all editathons</p>
      </div>
      <span v-if="!loading && selectedEditathon" class="info-badge">
        {{ selectedEditathon.count }} article{{ selectedEditathon.count !== 1 ? 's' : '' }}
      </span>
    </div>
    
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading article statistics...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <p>{{ error }}</p>
    </div>
    
    <div v-else-if="editathons.length === 0" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      <p>No editathons found</p>
    </div>
    
    <canvas v-else ref="chartCanvas"></canvas>
    
    <div v-if="!loading && editathons.length > 0" class="chart-info">
      <div v-if="selectedEditathon" class="selected-info">
        <div class="selected-name">{{ selectedEditathon.name }}</div>
        <div class="selected-meta">
          <span class="selected-count">{{ selectedEditathon.count }} articles</span>
          <span v-if="totalArticles > 0" class="selected-percent">
            {{ ((selectedEditathon.count / totalArticles) * 100).toFixed(1) }}% of total
          </span>
        </div>
      </div>
      <div v-else class="chart-hint">
        Click on a bar to see details
      </div>
      <div class="chart-total">
        Total: <strong>{{ totalArticles }}</strong> articles across <strong>{{ editathons.length }}</strong> editathons
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import Chart from 'chart.js/auto'
import { fetchEditathons } from '../services/api'

const chartCanvas = ref(null)
const editathons = ref([])
const loading = ref(true)
const error = ref(null)
const selectedEditathon = ref(null)
let chart = null

const totalArticles = computed(() => 
  editathons.value.reduce((sum, e) => sum + (e.article_count || 0), 0)
)

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
    console.error('ChartYearArticles error:', err)
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartCanvas.value || editathons.value.length === 0) return
  
  if (chart) {
    chart.destroy()
  }
  
  const sortedEdits = [...editathons.value].sort((a, b) => 
    (b.article_count || 0) - (a.article_count || 0)
  )
  
  const labels = sortedEdits.map(e => {
    const name = e.name || 'Unnamed'
    return name.length > 25 ? name.substring(0, 25) + '...' : name
  })
  const data = sortedEdits.map(e => e.article_count || 0)
  const maxValue = Math.max(...data)
  
  chart = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Articles',
        data,
        backgroundColor: (context) => {
          const value = context.parsed.y
          const ratio = maxValue > 0 ? value / maxValue : 0
          // Gradient from light blue to deep blue based on value
          const blue = Math.floor(43 + (130 * ratio))
          const green = Math.floor(140 + (95 * (1 - ratio)))
          return `rgb(${blue}, ${green}, 255)`
        },
        borderRadius: 6,
        borderSkipped: false,
        hoverBackgroundColor: (context) => {
          const value = context.parsed.y
          const ratio = maxValue > 0 ? value / maxValue : 0
          const blue = Math.floor(33 + (120 * ratio))
          const green = Math.floor(130 + (85 * (1 - ratio)))
          return `rgb(${blue}, ${green}, 255)`
        }
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: {
            color: '#374151',
            font: {
              size: 11
            },
            maxRotation: 45,
            minRotation: 0
          },
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: '#6b7280',
            font: {
              size: 11
            },
            stepSize: 1,
            callback: function(value) {
              return Number.isInteger(value) ? value : null
            }
          },
          grid: {
            color: '#e5e7eb',
            drawBorder: false
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
              return sortedEdits[idx]?.name || 'Unnamed'
            },
            label: (context) => {
              const count = context.parsed.y
              const percent = totalArticles.value > 0 
                ? ((count / totalArticles.value) * 100).toFixed(1)
                : 0
              return [
                `${count} article${count !== 1 ? 's' : ''}`,
                `${percent}% of total submissions`
              ]
            }
          }
        }
      },
      onClick: (_evt, elements) => {
        if (!elements?.length) {
          selectedEditathon.value = null
          return
        }
        const idx = elements[0].index
        const editathon = sortedEdits[idx]
        selectedEditathon.value = {
          name: editathon.name || 'Unnamed',
          count: editathon.article_count || 0
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

.info-badge {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  padding: 0.3rem 0.85rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.chart-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
}

.selected-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.selected-name {
  font-weight: 600;
  color: #111827;
  font-size: 0.9rem;
}

.selected-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #6b7280;
}

.selected-count {
  color: #3b82f6;
  font-weight: 500;
}

.selected-percent {
  color: #6b7280;
}

.chart-hint {
  font-size: 0.85rem;
  color: #9ca3af;
  font-style: italic;
}

.chart-total {
  font-size: 0.85rem;
  color: #6b7280;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

.chart-total strong {
  color: #111827;
  font-weight: 600;
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
  border-top-color: #3b82f6;
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
  
  .selected-meta {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>
