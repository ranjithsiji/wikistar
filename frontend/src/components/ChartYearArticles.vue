<template>
  <div class="card chart-card p-3">
    <h6>Articles by Editathon</h6>
    <canvas ref="c"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'
import { fetchEditathons } from '../services/api'

const c = ref(null)
onMounted(async ()=>{
  try {
    const edits = await fetchEditathons()
    const labels = edits.map(e => e.name.length > 20 ? e.name.substring(0, 20) + '...' : e.name)
    const data = edits.map(e => e.article_count || 0)

    new Chart(c.value.getContext('2d'), {
      type:'bar',
      data:{
        labels,
        datasets:[{
          label:'Articles',
          data,
          backgroundColor:'#2b8cff'
        }]
      },
      options:{
        responsive:true,
        plugins:{
          legend:{ display:false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          }
        }
      }
    })
  } catch (error) {
    console.error('Error loading chart:', error)
  }
})
</script>
