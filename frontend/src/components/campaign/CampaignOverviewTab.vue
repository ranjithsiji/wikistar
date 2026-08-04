<script setup>
import { computed } from 'vue'
import { CdxButton, CdxTable } from '@wikimedia/codex'

const props = defineProps({
  campaign: { type: Object, required: true },
  stats: { type: Object, default: null },
  // The preview paints before the leaderboard request lands, so an empty
  // list mid-flight is not the same as "there is no leaderboard".
  leaderboardLoading: { type: Boolean, default: false },
  // 'loading' | 'ready' | 'failed' — see CampaignView.vue.
  statsState: { type: String, default: 'ready' },
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
// Whole days from today to the end date, in the viewer's own timezone.
// The campaign carries its dates, so this needs no request at all.
const daysLeft = computed(() => {
  const end = props.campaign?.end_date
  if (!end) return null
  const [y, m, d] = end.split('-').map(Number)
  if (!y || !m || !d) return null
  const endOfDay = new Date(y, m - 1, d)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.round((endOfDay - today) / 86400000)
})
const daysLeftLabel = computed(() => {
  const n = daysLeft.value
  if (n === null) return null
  if (n < 0) return 'Ended'
  if (n === 0) return 'Last day'
  return String(n)
})

// Submissions and participants come with the campaign itself, so those
// two tiles fill immediately; only the rest wait on /stats. They used to
// sit blank alongside a header already displaying the same two numbers.
const overviewTiles = computed(() => [
  { label: 'Submissions', value: props.campaign?.submission_count, color: 'blue',
    instant: true },
  { label: 'Participants', value: props.campaign?.participant_count, color: 'green',
    instant: true },
  { label: 'Total points', value: props.stats?.total_points, color: 'violet' },
  { label: 'Days left', value: daysLeftLabel.value, color: 'amber', instant: true }
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
    <!-- Headline statistics: left-aligned, bottom accent bar per tile.
         Tiles marked `instant` read from the campaign itself and are
         always shown; the rest wait on /stats and are dropped entirely if
         it fails, since a row of blank tiles reads as "no activity". -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <template v-for="t in overviewTiles" :key="t.label">
        <div v-if="t.instant || statsState !== 'failed'" class="card overflow-hidden">
          <div class="p-4">
            <div class="text-xs font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
              {{ t.label }}
            </div>
            <!-- pulsing bar stands in for the number until stats arrive -->
            <div v-if="!t.instant && statsState === 'loading'"
                 class="h-8 mt-1 flex items-center" aria-hidden="true">
              <span class="block h-6 w-16 rounded animate-pulse bg-neutral-200 dark:bg-neutral-700"></span>
            </div>
            <div v-else class="text-3xl font-extrabold tabular-nums mt-1"
                 :class="tileClasses[t.color].text">
              {{ t.value ?? '—' }}
            </div>
          </div>
          <div class="h-1" :class="tileClasses[t.color].bar"></div>
        </div>
      </template>
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
              <a v-for="m in campaign.members.filter(m => m.role === 'organizer')" :key="m.id"
                 :href="`https://meta.wikimedia.org/wiki/User:${m.user.username.replaceAll(' ', '_')}`"
                 target="_blank" rel="noopener"
                 class="badge bg-link-50 text-link-700 dark:bg-link-950 dark:text-link-300 hover:underline">
                {{ m.user.username }}
              </a>
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

      <!-- Leaderboard preview: top 5, link through to the full tab. The card
           keeps its column even with no rows — hiding it left a wide blank
           gap beside the sidebar. -->
      <div class="card p-4">
        <div class="flex items-center justify-between mb-2">
          <h4 class="font-semibold text-base">Leaderboard preview</h4>
          <cdx-button v-if="leaderboardPreview.length"
                      action="progressive" weight="quiet" size="small"
                      @click="emit('view-leaderboard')">
            View full leaderboard →
          </cdx-button>
        </div>
        <!-- Placeholder rows rather than a message: the preview is a table,
             so a table-shaped skeleton reads as "this is filling in". -->
        <div v-if="leaderboardLoading && !leaderboardPreview.length"
             class="py-2" aria-busy="true" aria-label="Loading leaderboard">
          <div v-for="n in 5" :key="n"
               class="flex items-center gap-3 py-2 border-b border-neutral-100
                      dark:border-neutral-800 last:border-0">
            <span class="h-4 w-6 rounded animate-pulse bg-neutral-200 dark:bg-neutral-700"></span>
            <span class="h-4 flex-1 max-w-40 rounded animate-pulse bg-neutral-200 dark:bg-neutral-700"></span>
            <span class="h-4 w-10 ml-auto rounded animate-pulse bg-neutral-200 dark:bg-neutral-700"></span>
            <span class="h-4 w-14 rounded animate-pulse bg-neutral-200 dark:bg-neutral-700"></span>
            <span class="h-4 w-10 rounded animate-pulse bg-neutral-200 dark:bg-neutral-700"></span>
          </div>
        </div>
        <p v-else-if="!leaderboardPreview.length"
           class="text-sm text-neutral-500 dark:text-neutral-400 py-6 text-center">
          No leaderboard to show yet.
        </p>
        <cdx-table v-if="leaderboardPreview.length"
                   caption="Top participants" :hide-caption="true"
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
