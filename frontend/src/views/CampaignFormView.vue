<script setup>
// Phase 2: create/edit form with tabs —
//   General (name, slug, dates, wiki language)
//   Scoring (mode selector + rule editor, preloaded with the default
//            self-assessment preset from the backend)
//   Jury (usernames, jury_can_submit toggle)
//   Suggested pages (articles + Wikidata items)
defineProps({ slug: { type: String, default: null } })
</script>

<template>
  <div>
    <h1 class="h3 mb-3">{{ slug ? 'Edit campaign' : 'Create campaign' }}</h1>
    <p class="text-muted">Campaign form — implemented in phase 2.</p>
  </div>
</template>
