<script setup>
import { computed, onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'

const props = defineProps({ slug: { type: String, required: true } })
const stats = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    stats.value = (await api.campaignStats(props.slug)).data
  } catch (e) {
    error.value = errorMessage(e)
  }
})

const tiles = computed(() => stats.value ? [
  { label: 'Submissions', value: stats.value.submissions },
  { label: 'Participants', value: stats.value.participants },
  { label: 'Total points', value: stats.value.total_points },
  { label: 'Reviews', value: stats.value.reviews },
  { label: 'Pending claims', value: stats.value.pending_claims },
  { label: 'Awaiting review', value: stats.value.unreviewed_submissions },
  { label: 'Bytes added', value: stats.value.total_bytes_added.toLocaleString() },
  { label: 'New pages', value: stats.value.new_pages }
] : [])

const maxTimeline = computed(() =>
  Math.max(1, ...(stats.value?.timeline || []).map(d => d.submissions)))
const maxPoints = computed(() =>
  Math.max(1, ...(stats.value?.top_contributors || []).map(r => r.points)))
</script>

<template>
  <p v-if="error" class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
  <div v-else-if="!stats" class="text-neutral-500">Loading…</div>
  <div v-else class="space-y-6">
    <!-- stat tiles -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div v-for="t in tiles" :key="t.label" class="card p-4">
        <div class="text-2xl font-bold tabular-nums">{{ t.value }}</div>
        <div class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">{{ t.label }}</div>
      </div>
    </div>

    <!-- submissions over time: single series, direct value labels -->
    <div class="card p-4" v-if="stats.timeline.length">
      <h4 class="font-semibold text-sm mb-3">Submissions per day</h4>
      <div class="flex items-end gap-1 h-36 overflow-x-auto pb-1">
        <div v-for="d in stats.timeline" :key="d.date"
             class="flex flex-col items-center gap-1 min-w-8"
             :title="`${d.date}: ${d.submissions} submissions`">
          <span class="text-xs tabular-nums text-neutral-500">{{ d.submissions }}</span>
          <div class="w-5 rounded-t"
               :style="{ height: `${(d.submissions / maxTimeline) * 100}px`,
                         background: 'var(--viz-series)' }"></div>
          <span class="text-[10px] text-neutral-500 whitespace-nowrap">{{ d.date.slice(5) }}</span>
        </div>
      </div>
    </div>

    <!-- top contributors: single measure, labels in ink, bar carries magnitude -->
    <div class="card p-4" v-if="stats.top_contributors.length">
      <h4 class="font-semibold text-sm mb-3">Top contributors</h4>
      <div class="space-y-2">
        <div v-for="row in stats.top_contributors" :key="row.user.id"
             class="grid grid-cols-12 items-center gap-2 text-sm"
             :title="`${row.user.username}: ${row.points} points, ${row.submission_count} submissions`">
          <span class="col-span-3 truncate">{{ row.rank }}. {{ row.user.username }}</span>
          <div class="col-span-7 h-4 rounded bg-neutral-100 dark:bg-neutral-800">
            <div class="h-4 rounded"
                 :style="{ width: `${(row.points / maxPoints) * 100}%`,
                           background: 'var(--viz-series)' }"></div>
          </div>
          <span class="col-span-2 tabular-nums text-right">{{ row.points }}</span>
        </div>
      </div>
    </div>

    <!-- composition -->
    <div class="grid sm:grid-cols-2 gap-4">
      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-2">By type</h4>
        <div v-for="(n, k) in stats.by_kind" :key="k" class="flex justify-between text-sm py-0.5">
          <span>{{ k.replace('_', ' ') }}</span><span class="tabular-nums">{{ n }}</span>
        </div>
      </div>
      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-2">By status</h4>
        <div v-for="(n, k) in stats.by_status" :key="k" class="flex justify-between text-sm py-0.5">
          <span>{{ k }}</span><span class="tabular-nums">{{ n }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
