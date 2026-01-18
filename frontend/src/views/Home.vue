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
import { store } from '../store'

const editathons = ref([])

const filteredEditathons = computed(() => {
  if (!store.selectedLanguage) return editathons.value
  return editathons.value.filter(e => e.language === store.selectedLanguage)
})

const getStartDate = (editathon) => editathon.startDate || editathon.start_date || editathon.startDate
const getEndDate = (editathon) => editathon.endDate || editathon.end_date || editathon.endDate

const parseDate = (value) => {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

const isOngoing = (editathon) => {
  if (editathon.status === 'completed' || editathon.status === 'archived') return false
  if (editathon.status === 'active') return true

  const now = new Date()
  const start = parseDate(getStartDate(editathon))
  const end = parseDate(getEndDate(editathon))

  if (start && end) return start <= now && end >= now
  if (start && !end) return start <= now
  if (!start && end) return end >= now
  return false
}

const isFinished = (editathon) => {
  if (editathon.status === 'completed' || editathon.status === 'archived') return true
  const end = parseDate(getEndDate(editathon))
  return !!end && end < new Date()
}

const ongoingEditathons = computed(() => {
  return filteredEditathons.value.filter(isOngoing)
})

const finishedEditathons = computed(() => {
  return filteredEditathons.value.filter(isFinished)
})

onMounted(async () => {
  editathons.value = await fetchEditathons()
})
</script>
