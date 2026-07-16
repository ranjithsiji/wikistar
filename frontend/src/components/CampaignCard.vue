<script setup>
defineProps({ campaign: { type: Object, required: true } })

const statusStyles = {
  draft: 'bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300',
  active: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  finished: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  archived: 'bg-neutral-200 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
}
const modeLabels = { jury: 'Jury scoring', self: 'Self-assessment', hybrid: 'Hybrid' }
</script>

<template>
  <router-link :to="`/campaigns/${campaign.slug}`"
               class="card block p-4 hover:border-blue-400 dark:hover:border-blue-600 transition-colors">
    <div class="flex items-start justify-between gap-2">
      <h3 class="font-semibold">{{ campaign.name }}</h3>
      <span class="badge shrink-0" :class="statusStyles[campaign.status]">{{ campaign.status }}</span>
    </div>
    <p class="text-sm text-neutral-600 dark:text-neutral-300 mt-1 line-clamp-2">
      {{ campaign.description || 'No description' }}
    </p>
    <div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-neutral-600 dark:text-neutral-300">
      <span>{{ campaign.start_date }} → {{ campaign.end_date }}</span>
      <span>{{ campaign.wiki_domain }}</span>
      <span>{{ modeLabels[campaign.scoring_mode] }}</span>
    </div>
    <div class="mt-2 flex gap-4 text-xs text-neutral-600 dark:text-neutral-300">
      <span><b>{{ campaign.submission_count }}</b> submissions</span>
      <span><b>{{ campaign.participant_count }}</b> participants</span>
      <span><b>{{ campaign.review_count }}</b> reviews</span>
    </div>
  </router-link>
</template>
