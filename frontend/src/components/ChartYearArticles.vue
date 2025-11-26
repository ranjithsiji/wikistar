<template>
  <div class="card chart-card p-3">
    <h6>Articles by Year</h6>
    <canvas ref="c"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'
import { fetchEditathons } from '../services/api'

const c = ref(null)
onMounted(async ()=>{
  const edits = await fetchEditathons()
  const years = {}
  edits.forEach(e=>{
    (e.articles||[]).forEach(a=>{
      const y = a.addedOn ? new Date(a.addedOn).getFullYear() : new Date(e.startDate).getFullYear()
      years[y] = (years[y]||0)+1
    })
  })
  const labels = Object.keys(years).sort()
  new Chart(c.value.getContext('2d'), {
    type:'bar',
    data:{ labels, datasets:[{ label:'Articles', data: labels.map(l=>years[l]), backgroundColor:'#2b8cff' }]},
    options:{ responsive:true, plugins:{ legend:{ display:false } } }
  })
})
</script>
