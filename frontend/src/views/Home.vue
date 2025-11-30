<template>
  <div class="container container-max py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h3 mb-0">Editathons</h1>
      <router-link to="/create" class="btn btn-primary">Create New Editathon</router-link>
    </div>

    <!-- Timeline Component -->
    <EditathonTimeline />

    <h4 class="mt-4">Ongoing</h4>
    <div class="row mt-2">
      <div class="col-md-6" v-for="e in ongoingEditathons" :key="e.id">
        <EditathonCard :editathon="e" />
      </div>
    </div>

    <h4 class="mt-4">Finished</h4>
    <div class="row mt-2">
      <div class="col-md-6" v-for="e in finishedEditathons" :key="e.id">
        <EditathonCard :editathon="e" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchEditathons } from '../services/api'
import EditathonCard from '../components/EditathonCard.vue'
import EditathonTimeline from '../components/EditathonTimeline.vue'

const editathons = ref([])

const ongoingEditathons = computed(() => {
  const now = new Date()
  return editathons.value.filter(editathon => {
    if (!editathon.endDate) return true
    const endDate = new Date(editathon.endDate)
    return endDate >= now
  })
})

const finishedEditathons = computed(() => {
  const now = new Date()
  return editathons.value.filter(editathon => {
    if (!editathon.endDate) return false
    const endDate = new Date(editathon.endDate)
    return endDate < now
  })
})

onMounted(async () => {
  editathons.value = await fetchEditathons()
})
</script>
