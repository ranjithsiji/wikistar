<script setup>
// Phase 2: campaign dashboard with tabs —
//   Overview (stats, rules, suggested pages)
//   Submissions (table with live point breakdown; submit form)
//   My entries (self-assessment claim editor per submission)
//   Review (jury mode: score form / hybrid: claim verification queue)
//   Leaderboard
defineProps({ slug: { type: String, required: true } })
</script>

<template>
  <div>
    <h1 class="h3 mb-3">Campaign: {{ slug }}</h1>
    <p class="text-muted">Campaign dashboard — implemented in phase 2.</p>
  </div>
</template>
