<template>
  <div>
    <h4>Editathons You Participated In</h4>
    <div v-if="editathons.length === 0" class="info-message">
      You haven't participated in any editathons yet.
    </div>
    <div v-else class="editathon-list">
      <div v-for="editathon in editathons" :key="editathon.id" class="editathon-item">
        <div class="editathon-content">
          <div>
            <h5>{{ editathon.name }}</h5>
            <p>{{ editathon.description }}</p>
            <small class="date-range">
              {{ formatDate(editathon.start_date) }} - {{ formatDate(editathon.end_date) }}
            </small>
          </div>
          <div class="editathon-actions">
            <span class="status-badge" :class="editathon.status === 'finished' ? 'finished' : 'active'">
              {{ editathon.status }}
            </span>
            <router-link :to="`/editathon/${editathon.id}`" class="view-btn">
              View
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  user: String,
  editathons: Array
})

function formatDate(dateString) {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString()
}
</script>