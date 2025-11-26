<template>
  <div>
    <span v-for="j in juries" :key="j.id" class="badge me-1" :class="j.reviewed ? 'bg-success' : 'bg-secondary'">
      {{ j.username }}
    </span>
  </div>
</template>

<script setup>
defineProps({ juries: Array })
</script>
