<script setup>
import { computed } from 'vue'
import { CdxButton, CdxTable } from '@wikimedia/codex'

const props = defineProps({
  campaign: { type: Object, required: true },
  stats: { type: Object, default: null },
  leaderboard: { type: Array, required: true }
})
const emit = defineEmits(['view-leaderboard', 'show-details'])

// Stat tile accent colors: a bottom bar plus a matching value color.
const tileClasses = {
  blue: { bar: 'bg-blue-600 dark:bg-blue-500', text: 'text-blue-700 dark:text-blue-400' },
  green: { bar: 'bg-green-600 dark:bg-green-500', text: 'text-green-700 dark:text-green-400' },
  violet: { bar: 'bg-violet-600 dark:bg-violet-500', text: 'text-violet-700 dark:text-violet-400' },
  amber: { bar: 'bg-amber-500 dark:bg-amber-500', text: 'text-amber-700 dark:text-amber-400' },
  red: { bar: 'bg-red-700 dark:bg-red-600', text: 'text-red-700 dark:text-red-500' }
}
const overviewTiles = computed(() => [
  { label: 'Submissions', value: props.stats?.submissions, color: 'blue' },
  { label: 'Participants', value: props.stats?.participants, color: 'green' },
  { label: 'Total points', value: props.stats?.total_points, color: 'violet' },
  { label: 'Bytes added', value: props.stats?.total_bytes_added?.toLocaleString(), color: 'red' },
  { label: 'Languages', value: props.stats?.languages, color: 'amber' }
])

const leaderboardPreview = computed(() => props.leaderboard.slice(0, 5))
const lbPreviewColumns = [
  { id: 'rank', label: '#', textAlign: 'number' },
  { id: 'username', label: 'Participant' },
  { id: 'submission_count', label: 'Submissions', textAlign: 'number' },
  { id: 'bytes_added', label: 'Bytes', textAlign: 'number' },
  { id: 'points', label: 'Points', textAlign: 'number' }
]
const lbPreviewRows = computed(() => leaderboardPreview.value.map(r => ({
  rank: r.rank, username: r.user.username, submission_count: r.submission_count,
  bytes_added: r.bytes_added, points: r.points, user: r.user
})))
</script>

<template>
  <div class="space-y-4">
    <!-- headline statistics: left-aligned, bottom accent bar per tile -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
      <div v-for="t in overviewTiles" :key="t.label" class="card overflow-hidden">
        <div class="p-4">
          <div class="text-xs font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
            {{ t.label }}
          </div>
          <div class="text-3xl font-extrabold tabular-nums mt-1" :class="tileClasses[t.color].text">
            {{ t.value ?? '—' }}
          </div>
        </div>
        <div class="h-1" :class="tileClasses[t.color].bar"></div>
      </div>
    </div>

    <!-- sidebar (about + people) + leaderboard preview -->
    <div class="grid lg:grid-cols-[20rem_1fr] gap-4 items-start">
      <div class="card p-4 space-y-4">
        <div>
          <h4 class="font-semibold text-base mb-2">About campaign</h4>
          <p v-if="campaign.description" class="text-sm whitespace-pre-wrap text-neutral-700 dark:text-neutral-300">
            {{ campaign.description }}
          </p>
          <p v-else class="text-sm text-neutral-500 dark:text-neutral-400">No description yet.</p>
        </div>
        <div class="border-t border-neutral-100 dark:border-neutral-800 pt-3">
          <div class="text-xs font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-1.5">
            Organizers
          </div>
          <div class="flex flex-wrap gap-1.5">
            <template v-if="campaign.members.some(m => m.role === 'organizer')">
              <span v-for="m in campaign.members.filter(m => m.role === 'organizer')" :key="m.id"
                    class="badge bg-link-50 text-link-700 dark:bg-link-950 dark:text-link-300">
                {{ m.user.username }}
              </span>
            </template>
            <span v-else class="text-sm text-neutral-500 dark:text-neutral-400">—</span>
          </div>
        </div>
        <div class="border-t border-neutral-100 dark:border-neutral-800 pt-3">
          <div class="text-xs font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-1.5">
            Jury
          </div>
          <div class="flex flex-wrap gap-1.5">
            <template v-if="campaign.members.some(m => m.role === 'jury')">
              <span v-for="m in campaign.members.filter(m => m.role === 'jury')" :key="m.id"
                    class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
                {{ m.user.username }}
              </span>
            </template>
            <span v-else class="text-sm text-neutral-500 dark:text-neutral-400">—</span>
          </div>
        </div>
      </div>

      <!-- leaderboard preview: top 5, link through to the full tab -->
      <div class="card p-4" v-if="leaderboardPreview.length">
        <div class="flex items-center justify-between mb-2">
          <h4 class="font-semibold text-base">Leaderboard preview</h4>
          <cdx-button action="progressive" weight="quiet" size="small"
                      @click="emit('view-leaderboard')">
            View full leaderboard →
          </cdx-button>
        </div>
        <cdx-table caption="Top participants" :hide-caption="true"
                   :columns="lbPreviewColumns" :data="lbPreviewRows">
          <template #item-rank="{ item }">
            <span v-if="item === 1"
                  class="inline-flex items-center justify-center w-6 h-6 rounded-full
                         bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300
                         text-xs font-bold tabular-nums">{{ item }}</span>
            <span v-else class="tabular-nums text-neutral-500 dark:text-neutral-400">{{ item }}</span>
          </template>
          <template #item-username="{ item, row }">
            <button type="button" title="Show this participant's submissions"
                    class="font-medium text-link-700 dark:text-link-400 hover:underline"
                    @click="emit('show-details', row.user)">{{ item }}</button>
          </template>
          <template #item-bytes_added="{ item }">
            <span class="tabular-nums">{{ item.toLocaleString() }}</span>
          </template>
          <template #item-points="{ item, row }">
            <span v-if="row.rank === 1"
                  class="badge bg-green-600 text-white font-bold tabular-nums">{{ item }}</span>
            <span v-else class="tabular-nums font-semibold">{{ item }}</span>
          </template>
        </cdx-table>
      </div>
    </div>
  </div>
</template>
