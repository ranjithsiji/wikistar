<template>
  <div>
    <h4>Articles Submitted by You</h4>
    <div v-if="loading" class="text-center">
      <div class="spinner-border"></div>
    </div>
    <div v-else-if="articles.length === 0" class="alert alert-info">
      You haven't submitted any articles yet.
    </div>
    <div v-else class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Article Title</th>
            <th>Editathon</th>
            <th>Submitted</th>
            <th>Status</th>
            <th>Points</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="article in articles" :key="article.id">
            <td>{{ article.article_title }}</td>
            <td>{{ article.editathon }}</td>
            <td>{{ formatDate(article.submitted_date) }}</td>
            <td>
              <span class="badge" :class="getStatusBadge(article.status)">
                {{ article.status }}
              </span>
            </td>
            <td>{{ article.points || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: String,
  articles: {
    type: Array,
    default: () => []
  }
})

const loading = computed(() => false) // No loading needed since data comes from parent

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

function getStatusBadge(status) {
  const classes = {
    pending: 'bg-warning',
    approved: 'bg-success',
    rejected: 'bg-danger',
    reviewed: 'bg-info'
  }
  return classes[status] || 'bg-secondary'
}
</script>
