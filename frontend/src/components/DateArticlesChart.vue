<template>
  <div class="chart-card">
    <div class="chart-header">
      <div>
        <h3>Date Wise Article Statistics</h3>
        <p>Daily submissions with live counts</p>
      </div>
      <span class="live-pill">Live</span>
    </div>
    <canvas ref="chartCanvas"></canvas>
    <div class="chart-selection">
      Total days tracked: {{ labels.length }} · Total articles: {{ totalArticles }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  articles: {
    type: Array,
    default: () => []
  }
})

const chartCanvas = ref(null)
let chart
const labels = ref([])
const counts = ref([])

const totalArticles = computed(() => counts.value.reduce((sum, val) => sum + val, 0))

const aggregateData = () => {
  const grouped = {}
  props.articles.forEach(article => {
    if (!article?.addedOn) return
    const date = new Date(article.addedOn)
    if (Number.isNaN(date.getTime())) return
    const key = date.toISOString().slice(0, 10)
    grouped[key] = (grouped[key] || 0) + 1
  })

  const sortedKeys = Object.keys(grouped).sort()
  labels.value = sortedKeys.map(key => {
    const date = new Date(key)
    return date.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    })
  })
  counts.value = sortedKeys.map(key => grouped[key])
}

const renderChart = () => {
  if (!chartCanvas.value) return
  if (chart) {
    chart.destroy()
  }

  chart = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'line',
    data: {
      labels: labels.value,
      datasets: [
        {
          label: 'Articles per day',
          data: counts.value,
          fill: true,
          tension: 0.35,
          borderColor: '#ef4444',
          backgroundColor: ctx => {
            const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 300)
            gradient.addColorStop(0, 'rgba(239, 68, 68, 0.35)')
            gradient.addColorStop(1, 'rgba(239, 68, 68, 0.02)')
            return gradient
          },
          pointBackgroundColor: '#ffffff',
          pointBorderColor: '#ef4444',
          pointHoverRadius: 6,
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: { color: '#374151' },
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#6b7280', stepSize: 1 }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: context => `${context.parsed.y} articles`
          }
        }
      }
    }
  })
}

watch(
  () => props.articles,
  () => {
    aggregateData()
    renderChart()
  },
  { deep: true, immediate: true }
)

onMounted(() => {
  aggregateData()
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
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  height: 100%;
  max-height: 350px;
}

.chart-card canvas {
  width: 100%;
  min-height: 200px;
  max-height: 250px;
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
}

.chart-header p {
  margin: 0;
  color: #6b7280;
  font-size: 0.8rem;
}

.live-pill {
  background: #dbeafe;
  color: #1d4ed8;
  padding: 0.2rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.chart-selection {
  font-size: 0.85rem;
  color: #6b7280;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
}
</style>
