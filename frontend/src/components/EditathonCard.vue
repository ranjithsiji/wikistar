<template>
  <div class="card editathon-card mb-3">
    <div class="card-body">
      <h5 class="card-title">{{ editathon.name }}</h5>
      <p class="text-muted mb-1">{{ shortRange(editathon.startDate, editathon.endDate) }}</p>
      <p class="small text-muted">{{ editathon.description || '' }}</p>
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <span v-for="j in editathon.juries" :key="j.id" class="badge badge-jury me-1">{{ j.username }}</span>
        </div>
        <div>
          <router-link :to="`/editathon/${editathon.id}`" class="btn btn-sm btn-outline-primary me-2">Open</router-link>
          <router-link :to="`/editathon/${editathon.id}/judge`" class="btn btn-sm btn-primary">Judge</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
const props = defineProps({ editathon: Object })
function shortRange(s,e){
  if(!s || !e) return ''
  return `${new Date(s).toLocaleDateString()} — ${new Date(e).toLocaleDateString()}`
}
</script>
