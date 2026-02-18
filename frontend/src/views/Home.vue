<template>
  <div class="container container-max py-1">
    <div class="d-flex justify-content-end align-items-center mb-1">
      <router-link to="/create" class="btn btn-primary btn-sm" v-if="store.user" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">Create New Editathon</router-link>
    </div>

    <!-- Timeline Component -->
    <EditathonTimeline />

    <h6 class="mt-1 mb-1" style="font-size: 0.9rem; font-weight: 600;">Ongoing</h6>
    <div class="row mt-0 g-1">
      <div class="col-md-6" v-for="e in ongoingEditathons" :key="e.id">
        <EditathonCard :editathon="e" />
      </div>
    </div>

    <h6 class="mt-1 mb-1" style="font-size: 0.9rem; font-weight: 600;">Finished</h6>
    <div class="row mt-0 g-1">
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
