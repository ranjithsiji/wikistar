<script setup>
import { computed, ref, watch } from 'vue'
import { CdxButton, CdxTable } from '@wikimedia/codex'
import api, { errorMessage } from '../../api'

const props = defineProps({
  campaign: { type: Object, required: true },
  submissions: { type: Array, required: true },
  isOrganizer: { type: Boolean, default: false },
  currentUsername: { type: String, default: '' },
  isLoggedIn: { type: Boolean, default: false }
})
const emit = defineEmits(['refresh', 'show-details'])

const error = ref('')
const notice = ref('')
const busy = ref('')          // username currently being added, or 'mine'

// Names removed locally the moment their submission is created. `refresh`
// is an event, not a promise — Vue does not await the parent's handler —
// so the row used to linger until the reload happened to land, and stayed
// for good if that request was slow or failed. Dropping the name here
// makes the list correct immediately; the reload then reconciles it.
const justAdded = ref(new Set())

const bulkSubs = computed(() =>
  props.submissions.filter(s => s.kind === 'wikidata_edits'))

// Once the reloaded list confirms a name has a bulk submission, stop
// suppressing it locally — otherwise a submission later deleted could
// never reappear here.
watch(bulkSubs, (subs) => {
  if (!justAdded.value.size) return
  const confirmed = new Set(subs.map(s => s.user.username))
  const pending = [...justAdded.value].filter(n => !confirmed.has(n))
  if (pending.length !== justAdded.value.size) {
    justAdded.value = new Set(pending)
  }
})

// Everyone who submitted anything, minus everyone who already has a bulk
// submission: these are the participants whose Wikidata work outside their
// individual submissions is currently uncounted.
const missing = computed(() => {
  const withBulk = new Set(bulkSubs.value.map(s => s.user.username))
  const all = new Map()
  for (const s of props.submissions) all.set(s.user.username, s.user)
  return [...all.values()].filter(
    u => !withBulk.has(u.username) && !justAdded.value.has(u.username))
})

const iHaveBulk = computed(() =>
  bulkSubs.value.some(s => s.user.username === props.currentUsername))
const iHaveSubmitted = computed(() =>
  props.submissions.some(s => s.user.username === props.currentUsername))

const columns = [
  { id: 'username', label: 'Participant' },
  { id: 'statements', label: 'Statements', textAlign: 'number' },
  { id: 'terms', label: 'Label/desc edits', textAlign: 'number' },
  { id: 'excluded', label: 'Counted separately', textAlign: 'number' },
  { id: 'points', label: 'Points', textAlign: 'number' },
  { id: 'fetched', label: 'Last recalculated' },
  { id: 'actions', label: '' }
]
const rows = computed(() => bulkSubs.value.map(s => ({
  username: s.user.username,
  statements: s.metrics?.over_limit ? '—' : (s.metrics?.statements ?? 0),
  terms: s.metrics?.over_limit ? '—' : (s.metrics?.terms ?? 0),
  excluded: s.metrics?.excluded_qids?.length ?? 0,
  points: s.points,
  fetched: s.metadata_fetched_at || '',
  actions: s.id,
  id: s.id,
  over_limit: !!s.metrics?.over_limit,
  user: s.user
})))

// "3 hours ago" reads faster than a timestamp when the question is really
// "is this stale?"; the exact time stays in the title attribute.
function timeAgo (iso) {
  if (!iso) return 'never'
  const then = new Date(iso)
  const mins = Math.round((Date.now() - then.getTime()) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.round(hours / 24)
  return days === 1 ? 'yesterday' : `${days} days ago`
}
const exactTime = (iso) => (iso ? new Date(iso).toLocaleString() : '')

// One participant at a time: an organizer chasing a single late edit does
// not need to re-walk everyone's contribution history, which is the whole
// cost of "Recalculate all".
const recalcOne = ref(0)          // submission id in flight
async function recalculate (id, username) {
  recalcOne.value = id
  error.value = ''
  notice.value = ''
  try {
    await api.recalculateSubmission(id)
    notice.value = `Recalculated ${username}'s Wikidata edits.`
    emit('refresh')
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    recalcOne.value = 0
  }
}

// Organizers: re-fetch every existing bulk submission's counts. Each user
// costs a contribution-history walk, so this can take a few seconds.
const recalcBusy = ref(false)
async function recalculateAll () {
  recalcBusy.value = true
  error.value = ''
  notice.value = ''
  try {
    const r = await api.recalculateAllBulkWikidata(props.campaign.slug)
    const d = r.data || {}
    notice.value = `Recalculated ${d.refreshed || 0} of ${d.total || 0}` +
      (d.over_limit ? `, ${d.over_limit} need manual scoring` : '') +
      (d.failed ? `, ${d.failed} failed` : '') + '.'
    emit('refresh')
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    recalcBusy.value = false
  }
}

async function add (username) {
  busy.value = username || 'mine'
  error.value = ''
  notice.value = ''
  try {
    const payload = { kind: 'wikidata_edits' }
    if (username) payload.username = username
    await api.createSubmission(props.campaign.slug, payload)
    // Drop the name now rather than waiting for the reload to land.
    if (username) {
      justAdded.value = new Set([...justAdded.value, username])
    }
    notice.value = username
      ? `Added a Wikidata edits submission for ${username}.`
      : 'Your Wikidata edits submission was added.'
    emit('refresh')
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div class="space-y-4">
    <p v-if="error" class="text-sm text-red-700 dark:text-red-400">{{ error }}</p>
    <p v-if="notice" class="text-sm text-green-700 dark:text-green-400">{{ notice }}</p>

    <div class="card p-4">
      <h4 class="font-semibold text-base mb-1">Wikidata bulk submissions</h4>
      <p class="text-sm text-neutral-600 dark:text-neutral-300">
        An individual item submission scores only that item. A bulk
        submission counts the rest of a participant's Wikidata work in the
        campaign window — including items that are not on the suggested
        list. Items already submitted individually are excluded here, so
        nothing is counted twice.
      </p>

      <!-- Participant: add my own if I missed it -->
      <div v-if="isLoggedIn && !iHaveBulk && iHaveSubmitted"
           class="mt-3 rounded-lg border border-amber-300 dark:border-amber-800
                  bg-amber-50 dark:bg-amber-950/40 p-3 flex flex-wrap
                  items-center justify-between gap-2">
        <span class="text-sm">
          You have no Wikidata bulk submission — your edits outside your
          individual submissions are not being counted.
        </span>
        <cdx-button action="progressive" weight="primary" size="small"
                    :disabled="!!busy" @click="add('')">
          {{ busy === 'mine' ? 'Adding…' : 'Add mine' }}
        </cdx-button>
      </div>
    </div>

    <!-- Organizers: who is missing one, with an Add button each -->
    <div v-if="isOrganizer" class="card p-4">
      <h4 class="font-semibold text-base mb-2">
        No bulk submission yet ({{ missing.length }})
      </h4>
      <p v-if="!missing.length" class="text-sm text-neutral-600 dark:text-neutral-300">
        Every participant who has submitted has a Wikidata bulk submission.
      </p>
      <template v-else>
        <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-3">
          These participants submitted individual pages but have no Wikidata
          bulk submission, so their other Wikidata edits score nothing.
        </p>
        <!-- One square cell per participant: the name on its own line above
             a full-width button, so long usernames wrap instead of
             squeezing the control down to a word. -->
        <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="u in missing" :key="u.username"
               class="rounded-lg border border-neutral-200 dark:border-neutral-800
                      bg-neutral-50 dark:bg-neutral-900/40 p-3 flex flex-col gap-2">
            <span class="text-sm font-medium break-words" :title="u.username">
              {{ u.username }}
            </span>
            <cdx-button action="progressive" weight="primary" class="w-full"
                        :disabled="!!busy" @click="add(u.username)">
              {{ busy === u.username ? 'Adding…' : 'Add bulk submission' }}
            </cdx-button>
          </div>
        </div>
      </template>
    </div>

    <div class="card p-4">
      <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
        <h4 class="font-semibold text-base">
          Bulk submissions ({{ bulkSubs.length }})
        </h4>
        <cdx-button v-if="isOrganizer && bulkSubs.length"
                    action="progressive" :disabled="recalcBusy"
                    @click="recalculateAll">
          {{ recalcBusy ? 'Recalculating…' : 'Recalculate all' }}
        </cdx-button>
      </div>
      <p v-if="recalcBusy" class="text-xs text-neutral-600 dark:text-neutral-300 mb-2">
        Fetching each participant's Wikidata history — this can take a
        few seconds.
      </p>
      <p v-if="!bulkSubs.length" class="text-sm text-neutral-600 dark:text-neutral-300">
        No Wikidata bulk submissions yet.
      </p>
      <cdx-table v-else caption="Wikidata bulk submissions" :hide-caption="true"
                 :columns="columns" :data="rows">
        <template #item-username="{ item, row }">
          <button type="button" class="font-medium text-link-700 dark:text-link-400 hover:underline"
                  @click="emit('show-details', row.user)">{{ item }}</button>
          <span v-if="row.over_limit"
                class="badge ml-2 bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300">
            needs manual scoring
          </span>
        </template>
        <template #item-points="{ item }">
          <span class="tabular-nums font-semibold">{{ item }}</span>
        </template>
        <template #item-fetched="{ item }">
          <span class="text-sm whitespace-nowrap"
                :class="item ? 'text-neutral-600 dark:text-neutral-300'
                             : 'text-amber-700 dark:text-amber-400'"
                :title="exactTime(item)">{{ timeAgo(item) }}</span>
        </template>
        <template #item-actions="{ row }">
          <cdx-button v-if="isOrganizer" weight="quiet" size="small"
                      :disabled="recalcOne === row.id || recalcBusy"
                      title="Refetch just this participant's Wikidata history"
                      @click="recalculate(row.id, row.username)">
            {{ recalcOne === row.id ? 'Recalculating…' : 'Recalculate' }}
          </cdx-button>
        </template>
      </cdx-table>
    </div>
  </div>
</template>
