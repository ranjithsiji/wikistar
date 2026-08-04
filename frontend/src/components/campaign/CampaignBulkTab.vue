<script setup>
import { computed, ref } from 'vue'
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

const bulkSubs = computed(() =>
  props.submissions.filter(s => s.kind === 'wikidata_edits'))

// Everyone who submitted anything, minus everyone who already has a bulk
// submission: these are the participants whose Wikidata work outside their
// individual submissions is currently uncounted.
const missing = computed(() => {
  const withBulk = new Set(bulkSubs.value.map(s => s.user.username))
  const all = new Map()
  for (const s of props.submissions) all.set(s.user.username, s.user)
  return [...all.values()].filter(u => !withBulk.has(u.username))
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
  { id: 'points', label: 'Points', textAlign: 'number' }
]
const rows = computed(() => bulkSubs.value.map(s => ({
  username: s.user.username,
  statements: s.metrics?.over_limit ? '—' : (s.metrics?.statements ?? 0),
  terms: s.metrics?.over_limit ? '—' : (s.metrics?.terms ?? 0),
  excluded: s.metrics?.excluded_qids?.length ?? 0,
  points: s.points,
  over_limit: !!s.metrics?.over_limit,
  user: s.user
})))

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
        <div class="flex flex-wrap gap-2">
          <span v-for="u in missing" :key="u.username"
                class="inline-flex items-center gap-2 rounded-full border
                       border-neutral-200 dark:border-neutral-800 pl-3 pr-1 py-1">
            <span class="text-sm">{{ u.username }}</span>
            <cdx-button weight="quiet" size="small" :disabled="!!busy"
                        @click="add(u.username)">
              {{ busy === u.username ? '…' : 'Add' }}
            </cdx-button>
          </span>
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
      </cdx-table>
    </div>
  </div>
</template>
