<template>
  <div class="card editathon-card mb-0" v-if="editathon">
    <div class="card-body" style="padding: 0.4rem;">
      <div class="d-flex justify-content-between align-items-start mb-0">
        <router-link :to="`/editathon/${editathon.id}`" class="card-title-link">
          <h6 class="card-title mb-0" style="font-size: 0.85rem;">{{ editathon.name || 'Unnamed Editathon' }}</h6>
        </router-link>
      </div>
      <p class="text-muted mb-0" style="font-size: 0.7rem;">{{ shortRange(editathon.startDate, editathon.endDate) }}</p>
      <p class="text-muted meta-line mb-0" style="font-size: 0.7rem;">
        {{ (editathon.language || 'en').toUpperCase() }} · {{ editathon.project || 'Wikimedia Project' }}
      </p>
      <p class="text-muted mb-0" style="font-size: 0.7rem; line-height: 1.2;">{{ editathon.description || '' }}</p>
      <div style="margin-top: 0.2rem;">
        <span v-for="j in (editathon.juries || [])" :key="j.id" class="badge badge-jury me-1" style="font-size: 0.65rem; padding: 0.1rem 0.3rem;">{{ j.username }}</span>
      </div>
    </div>
  </div>
  <div v-else class="card editathon-card mb-0">
    <div class="card-body" style="padding: 0.4rem;">
      <p class="text-muted small">Loading editathon...</p>
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
