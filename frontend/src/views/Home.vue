<template>
  <div class="container container-max py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h3 mb-0">Editathons</h1>
      <router-link to="/create" class="btn btn-primary">Create New Editathon</router-link>
    </div>

    <div class="row g-3">
      <div class="col-lg-6 col-md-12">
        <ChartYearArticles />
      </div>
      <div class="col-lg-6 col-md-12">
        <ChartTimeline />
      </div>
    </div>

    <h4 class="mt-4">Finished</h4>
    <div class="row mt-2">
      <div class="col-md-6" v-for="e in editathons" :key="e.id">
        <EditathonCard :editathon="e" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchEditathons } from '../services/api'
import ChartYearArticles from '../components/ChartYearArticles.vue'
import ChartTimeline from '../components/ChartTimeline.vue'
import EditathonCard from '../components/EditathonCard.vue'

const editathons = ref([])

onMounted(async ()=>{
  editathons.value = await fetchEditathons()
})
</script>
