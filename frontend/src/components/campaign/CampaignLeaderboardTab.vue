<script setup>
import { computed, ref } from 'vue'
import { CdxTable } from '@wikimedia/codex'
import UserAvatar from '../UserAvatar.vue'

const props = defineProps({
  leaderboard: { type: Array, required: true },
  currentUsername: { type: String, default: '' },
  showPodium: { type: Boolean, default: true },
  // Needed to build each participant's on-wiki contributions link:
  // which wiki, and the campaign window to scope it to.
  campaign: { type: Object, default: null }
})
const emit = defineEmits(['show-details'])

// Link to a participant's contributions, limited to the campaign
// period: Special:Contributions takes the bounds as start/end dates, so
// the list opens on the work that counts here rather than the user's
// entire history.
//
// A multi-language campaign has no single target wiki -- entries come
// from whichever Wikipedia the participant wrote in -- so those link to
// the cross-wiki view on Meta instead of picking one wiki and being
// wrong for everyone who used another.
function contributionsUrl (username) {
  const campaign = props.campaign
  if (!campaign || !username) return null
  if (campaign.settings?.multi_language) {
    return 'https://meta.wikimedia.org/wiki/Special:CentralAuth/' +
      encodeURIComponent(username.replace(/ /g, '_'))
  }
  const domain = campaign.wiki_domain
  if (!domain) return null
  const params = new URLSearchParams({
    target: username,
    start: campaign.start_date || '',
    end: campaign.end_date || ''
  })
  return `https://${domain}/wiki/Special:Contributions?${params}`
}

// The tooltip has to describe whichever of the two links this is.
function contributionsTitle (username) {
  if (props.campaign?.settings?.multi_language) {
    return `See ${username}'s accounts and contributions across wikis`
  }
  return `See ${username}'s contributions to ` +
    `${props.campaign?.wiki_domain} during the campaign`
}

const lbColumns = [
  { id: 'rank', label: '#', textAlign: 'number' },
  { id: 'username', label: 'Participant', allowSort: true },
  // The bar is its own column so the counts beside it line up in a
  // clean numeric column instead of being pushed around by bar width.
  // It has no sort of its own: it renders the same value as
  // "Submissions", which is the sortable one.
  { id: 'submission_bar', label: 'Share', textAlign: 'number' },
  { id: 'submission_count', label: 'Submissions', textAlign: 'number', allowSort: true },
  { id: 'bytes_added', label: 'Bytes', textAlign: 'number', allowSort: true },
  { id: 'points', label: 'Points', textAlign: 'number', allowSort: true }
]
const lbSort = ref({})
const lbRows = computed(() => {
  const rows = props.leaderboard.map(r => ({
    rank: r.rank, username: r.user.username,
    submission_bar: r.submission_count, submission_count: r.submission_count,
    bytes_added: r.bytes_added, points: r.points, user: r.user
  }))
  const [key, dir] = Object.entries(lbSort.value)[0] || []
  if (!key) return rows  // server order (ranked) when no explicit sort
  const mul = dir === 'asc' ? 1 : -1
  return rows.sort((a, b) => {
    const va = key === 'username' ? a.username.toLowerCase() : a[key]
    const vb = key === 'username' ? b.username.toLowerCase() : b[key]
    return (va < vb ? -1 : va > vb ? 1 : 0) * mul
  })
})
function onLbSort (newSort) {
  const active = Object.entries(newSort).find(([, dir]) => dir !== 'none')
  lbSort.value = active ? { [active[0]]: active[1] } : {}
}
const myLeaderboardRow = computed(() =>
  props.leaderboard.find(r => r.user.username === props.currentUsername) || null)
const maxSubmissions = computed(() =>
  Math.max(1, ...props.leaderboard.map(r => r.submission_count)))

// Podium: top 3, ordered 2nd / 1st / 3rd for the visual layout.
const podium = computed(() => {
  const [first, second, third] = props.leaderboard
  return [second, first, third].filter(Boolean)
})
// How far the leader is ahead of the runner-up — a real, computed summary
// (not a fabricated trend).
const leadMargin = computed(() => {
  const [first, second] = props.leaderboard
  return first && second ? Math.round((first.points - second.points) * 100) / 100 : null
})
</script>

<template>
  <div class="space-y-4">
    <p v-if="!leaderboard.length" class="text-neutral-600 dark:text-neutral-300">No points yet.</p>

    <template v-else>
      <!-- podium: top 3, 1st raised and highlighted in the middle -->
      <div v-if="showPodium" class="grid grid-cols-3 gap-3 items-end">
        <div v-for="row in podium" :key="row.user.id"
             class="card p-4 text-center cursor-pointer hover:border-blue-300 dark:hover:border-blue-700"
             :class="row.rank === 1
               ? 'border-2 border-blue-700 dark:border-blue-500 sm:pb-6 order-2'
               : row.rank === 2 ? 'order-1' : 'order-3'"
             @click="emit('show-details', row.user)">
          <UserAvatar :username="row.user.username" :size="row.rank === 1 ? 'lg' : 'md'" class="mx-auto" />
          <span class="badge mt-2"
                :class="row.rank === 1
                  ? 'bg-blue-700 text-white'
                  : row.rank === 2 ? 'bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300'
                  : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'">
            {{ row.rank === 1 ? '★ 1st' : row.rank === 2 ? '2nd' : '3rd' }}
          </span>
          <div class="font-semibold mt-1.5 truncate">{{ row.user.username }}</div>
          <div class="text-xl font-extrabold tabular-nums mt-1">
            {{ row.points }} <span class="text-xs font-normal text-neutral-500 dark:text-neutral-400">pts</span>
          </div>
          <div class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            {{ row.submission_count }} submission{{ row.submission_count === 1 ? '' : 's' }}
          </div>
        </div>
      </div>

      <!-- lead margin: a real, computed summary — never a fabricated trend -->
      <div v-if="showPodium && leadMargin" class="card p-4 flex items-center gap-3">
        <span class="inline-flex items-center justify-center w-9 h-9 rounded-full shrink-0
                     bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
          </svg>
        </span>
        <p class="text-sm">
          <b>{{ podium[1]?.user.username }}</b> is leading by
          <b class="text-blue-700 dark:text-blue-400">{{ leadMargin }} point{{ leadMargin === 1 ? '' : 's' }}</b>
          over the runner-up.
        </p>
      </div>

      <!-- personal stats: the logged-in user's own row, pulled out front -->
      <div v-if="myLeaderboardRow" class="card border-2 p-4 text-center border-blue-400 dark:border-blue-700">
        <h4 class="font-semibold text-sm mb-3 text-neutral-900 dark:text-neutral-100">Your statistics</h4>
        <div class="grid grid-cols-3 divide-x divide-neutral-200 dark:divide-neutral-800">
          <div>
            <div class="text-2xl font-extrabold tabular-nums text-blue-700 dark:text-blue-400">
              {{ myLeaderboardRow.submission_count }}
            </div>
            <div class="text-xs font-medium mt-1">Contributions</div>
          </div>
          <div>
            <div class="text-2xl font-extrabold tabular-nums text-blue-700 dark:text-blue-400">
              {{ myLeaderboardRow.points }}
            </div>
            <div class="text-xs font-medium mt-1">Points</div>
          </div>
          <div>
            <div class="text-2xl font-extrabold tabular-nums text-blue-700 dark:text-blue-400">
              {{ myLeaderboardRow.bytes_added.toLocaleString() }}
            </div>
            <div class="text-xs font-medium mt-1">Bytes</div>
          </div>
        </div>
      </div>

      <!-- complete standings -->
      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-3">Complete standings</h4>
        <cdx-table caption="Leaderboard" :hide-caption="true"
                   :columns="lbColumns" :data="lbRows"
                   :sort="lbSort" @update:sort="onLbSort">
          <template #item-rank="{ item }">
            <!-- min-w keeps the top-3 medals circular while letting a
                 three-digit rank widen rather than wrap. -->
            <span class="inline-flex items-center justify-center min-w-6 h-6 px-1 rounded-full text-xs font-bold tabular-nums whitespace-nowrap"
                  :class="item === 1 ? 'bg-blue-700 text-white'
                    : item === 2 ? 'bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300'
                    : item === 3 ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                    : 'text-neutral-500 dark:text-neutral-400'">
              {{ item }}
            </span>
          </template>
          <template #item-username="{ item, row }">
            <button type="button" title="Show this participant's submissions"
                    class="inline-flex items-center gap-2 font-medium text-link-700 dark:text-link-400 hover:underline"
                    @click="emit('show-details', row.user)">
              <UserAvatar :username="item" size="sm" />
              {{ item }}
            </button>
          </template>
          <template #item-submission_bar="{ item }">
            <div class="w-16 h-2 rounded bg-neutral-100 dark:bg-neutral-800 inline-block align-middle"
                 role="img"
                 :aria-label="`${item} of ${maxSubmissions} submissions by the most active participant`"
                 :title="`${item} submissions`">
              <div class="h-2 rounded bg-blue-600 dark:bg-blue-500"
                   :style="{ width: `${(item / maxSubmissions) * 100}%` }"></div>
            </div>
          </template>
          <template #item-submission_count="{ item, row }">
            <a v-if="contributionsUrl(row.username)"
               :href="contributionsUrl(row.username)" target="_blank" rel="noopener"
               class="tabular-nums whitespace-nowrap text-link-700 dark:text-link-400 hover:underline"
               :title="contributionsTitle(row.username)">
              {{ item }}
            </a>
            <span v-else class="tabular-nums whitespace-nowrap">{{ item }}</span>
          </template>
          <template #item-bytes_added="{ item }">
            <span class="tabular-nums">{{ item.toLocaleString() }}</span>
          </template>
          <template #item-points="{ item, row }">
            <span v-if="row.rank === 1" class="badge bg-green-600 text-white font-bold tabular-nums">{{ item }}</span>
            <span v-else class="tabular-nums font-semibold">{{ item }}</span>
          </template>
        </cdx-table>
      </div>
    </template>
  </div>
</template>
