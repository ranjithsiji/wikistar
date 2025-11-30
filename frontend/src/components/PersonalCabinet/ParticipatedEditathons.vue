<template>
  <div class="participated-section">
    <h2 class="section-title">Participated Editathons</h2>
    
    <div v-if="editathons.length === 0" class="empty-state">
      <p>You haven't participated in any editathons yet.</p>
    </div>
    
    <div v-else class="editathons-list">
      <div v-for="editathon in editathons" :key="editathon.id" class="editathon-box">
        <div class="box-header">
          <h3 class="box-title">{{ editathon.name }}</h3>
          <span class="status-badge" :class="editathon.status === 'finished' ? 'finished' : 'active'">
            {{ editathon.status }}
          </span>
        </div>
        
        <p class="box-description">{{ editathon.description }}</p>
        
        <div class="box-meta">
          <div class="meta-item">
            <span class="meta-label">Duration:</span>
            <span class="meta-value">
              {{ formatDate(editathon.start_date) }} - {{ formatDate(editathon.end_date) }}
            </span>
          </div>
          <router-link :to="`/editathon/${editathon.id}`" class="view-link">
            View Editathon →
          </router-link>
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

<style scoped>
.participated-section {
  padding: 1rem 0;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  background: #f9fafb;
  border: 2px dashed #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  font-weight: 500;
}

.editathons-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.editathon-box {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.editathon-box:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.box-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.box-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.status-badge {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.active {
  background: #dcfce7;
  color: #166534;
}

.status-badge.finished {
  background: #e0e7ff;
  color: #312e81;
}

.box-description {
  color: #6b7280;
  font-size: 0.95rem;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.box-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meta-value {
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 600;
}

.view-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.view-link:hover {
  color: #5568d3;
  text-decoration: underline;
}
</style>