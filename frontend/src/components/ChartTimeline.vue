<template>
  <div class="card chart-card p-3">
    <h6>Editathon timeline</h6>
    <canvas ref="c"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'
import 'chartjs-adapter-date-fns'
import { fetchEditathons } from '../services/api'

const c = ref(null)
onMounted(async ()=>{
  const edits = await fetchEditathons()
  const labels = edits.map(e=>e.name)
  const dataPoints = edits.map(e=>{
    const start = new Date(e.startDate).getTime()
    const end = new Date(e.endDate).getTime()
    return { x:[start,end], y: e.name }
  })
  
  // Determine color based on status (ongoing vs finished)
  const backgroundColor = edits.map(e => {
    const now = new Date().getTime()
    const endDate = new Date(e.endDate).getTime()
    // Green for ongoing, grey for finished
    return endDate > now ? '#16a34a' : '#9ca3af'
  })
  
  new Chart(c.value.getContext('2d'), {
    type:'bar',
    data:{ 
      labels, 
      datasets:[{ 
        label:'Duration', 
        data: dataPoints, 
        backgroundColor: backgroundColor
      }]
    },
    options:{
      indexAxis:'y',
      parsing:{ xAxisKey:'x', yAxisKey:'y' },
      scales:{ x:{ type:'time', time:{ unit:'month' } }, y:{ ticks:{ autoSkip:false } } },
      responsive:true
    }
  })
})
</script>
