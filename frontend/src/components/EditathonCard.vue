<template>
  <div class="card editathon-card mb-3" v-if="editathon">
    <div class="card-body">
      <div class="d-flex justify-content-between align-items-start mb-2">
        <router-link :to="`/editathon/${editathon.id}`" class="card-title-link">
          <h5 class="card-title mb-0">{{ editathon.name || 'Unnamed Editathon' }}</h5>
        </router-link>
      </div>
      <p class="text-muted mb-1">{{ shortRange(editathon.startDate, editathon.endDate) }}</p>
      <p class="small text-muted meta-line">
        {{ (editathon.language || 'en').toUpperCase() }} · {{ editathon.project || 'Wikimedia Project' }}
      </p>
      <p class="small text-muted">{{ editathon.description || '' }}</p>
      <div>
        <span v-for="j in (editathon.juries || [])" :key="j.id" class="badge badge-jury me-1">{{ j.username }}</span>
      </div>
    </div>
  </div>
  <div v-else class="card editathon-card mb-3">
    <div class="card-body">
      <p class="text-muted">Loading editathon...</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  editathon: {
    type: Object,
    required: true
  }
})

const shortRange = (start, end) => {
  if (!start || !end) return ''
  const startDate = new Date(start).toLocaleDateString()
  const endDate = new Date(end).toLocaleDateString()
  return `${startDate} - ${endDate}`
}

const isFinished = (editathon) => {
  if (!editathon.endDate) return false
  const endDate = new Date(editathon.endDate)
  const now = new Date()
  return endDate < now
}
</script>
