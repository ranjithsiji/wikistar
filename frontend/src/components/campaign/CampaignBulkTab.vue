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

// Freshly recalculated rows, by submission id. The recalculate response
// already carries the updated submission, but `refresh` is an event rather
// than a promise, so the table would otherwise keep showing the old counts
// and time until the parent's reload happened to land — and keep them for
// good if it failed. Applying the response here makes the row correct
// immediately; an entry is dropped once the reload confirms it.
const updated = ref({})

const bulkSubs = computed(() =>
  props.submissions.filter(s => s.kind === 'wikidata_edits'))

// Once the reloaded list confirms a name has a bulk submission, stop
// suppressing it locally — otherwise a submission later deleted could
// never reappear here.
watch(bulkSubs, (subs) => {
  if (justAdded.value.size) {
    const confirmed = new Set(subs.map(s => s.user.username))
    const pending = [...justAdded.value].filter(n => !confirmed.has(n))
    if (pending.length !== justAdded.value.size) {
      justAdded.value = new Set(pending)
    }
  }
  // Drop a local copy once the reloaded row is at least as fresh, so the
  // override cannot mask a later change made elsewhere.
  const ids = Object.keys(updated.value)
  if (!ids.length) return
  const still = {}
  for (const id of ids) {
    const server = subs.find(s => String(s.id) === String(id))
    // Gone from the list (withdrawn/deleted) — nothing left to override.
    if (!server) continue
    const local = updated.value[id]
    if (!(server.metadata_fetched_at >= local.metadata_fetched_at)) {
      still[id] = local
    }
  }
  if (Object.keys(still).length !== ids.length) updated.value = still
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
const rows = computed(() => bulkSubs.value.map(raw => {
  // Prefer a just-recalculated copy over the list's stale one.
  const s = updated.value[raw.id] || raw
  return {
    username: s.user.username,
    statements: s.metrics?.over_limit ? '—' : (s.metrics?.statements ?? 0),
    terms: s.metrics?.over_limit ? '—' : (s.metrics?.terms ?? 0),
    excluded: s.metrics?.excluded_qids?.length ?? 0,
    points: s.points,
    fetched: s.metadata_fetched_at || '',
    actions: s.id,
    id: s.id,
    over_limit: !!s.metrics?.over_limit,
    limit: s.metrics?.limit ?? null,
    user: s.user
  }
}))

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
// Rows the sweep deliberately leaves alone: it runs against the lower
// sweep cap, so a participant above it is skipped every time. Scoring them
// is the individual Recalculate, which uses the higher cap.
const stuckRows = computed(() => rows.value.filter(r => r.over_limit))

// The two limits actually in force for this campaign. A campaign saved
// before a limit's default changed keeps its old value as a stored
// override, which silently beats the new default — so show the effective
// numbers rather than letting an organizer assume the defaults apply.
const autoCap = computed(() =>
  props.campaign?.settings?.wikidata_edit_limit_single ?? null)
const sweepCap = computed(() =>
  props.campaign?.settings?.max_wikidata_edits_sweep ?? null)
// The individual limit is meant to be the generous one; when it is not,
// recalculating a heavy editor cannot succeed however often it is tried.
const capsLookWrong = computed(() =>
  autoCap.value !== null && sweepCap.value !== null
  && autoCap.value <= sweepCap.value)

async function recalculate (id, username) {
  recalcOne.value = id
  error.value = ''
  notice.value = ''
  try {
    const r = await api.recalculateSubmission(id)
    const sub = r?.data
    if (sub) updated.value = { ...updated.value, [id]: sub }
    // Report what actually came back. "Recalculated." alone left the
    // organizer to read the row and guess whether it had worked — the
    // interesting outcomes are a score, a genuine zero, and still being
    // over the cap, which all look similar at a glance.
    const m = sub?.metrics || {}
    if (m.over_limit) {
      error.value = `${username} has more than ${m.limit} Wikidata edits in `
        + 'the campaign window — too many to score automatically. Enter the '
        + 'points manually with a points override.'
    } else {
      const st = m.statements ?? 0
      const tm = m.terms ?? 0
      const detail = `${st} statement${st === 1 ? '' : 's'}, `
        + `${tm} label/description edit${tm === 1 ? '' : 's'}`
      notice.value = (st || tm)
        ? `${username}: ${sub.points} point${sub.points === 1 ? '' : 's'} `
          + `from ${detail}.`
        : `${username}: no countable Wikidata edits found in the campaign `
          + 'window (0 points).'
    }
    emit('refresh')
  } catch (e) {
    error.value = `Could not recalculate ${username}: ${errorMessage(e)}`
  } finally {
    recalcOne.value = 0
  }
}

// Removing a bulk submission. The backend already allows it (an owner may
// withdraw their own while the campaign runs; an organizer may delete
// any) — but with these rows off the submissions list, this tab is now
// the only place the action exists.
const removing = ref(0)
const campaignActive = computed(() => props.campaign?.status === 'active')
const canRemove = (row) =>
  props.isOrganizer
  || (row.user.username === props.currentUsername && campaignActive.value)
async function remove (row) {
  const mine = row.user.username === props.currentUsername
  const question = mine
    ? 'Withdraw your Wikidata edits submission? Its points are removed.'
    : `Delete ${row.user.username}'s Wikidata edits submission? `
      + 'Its points are removed.'
  if (!confirm(question)) return
  removing.value = row.id
  error.value = ''
  notice.value = ''
  try {
    await api.deleteSubmission(row.id)
    notice.value = mine
      ? 'Your Wikidata edits submission was withdrawn.'
      : `Removed ${row.user.username}'s Wikidata edits submission.`
    emit('refresh')
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    removing.value = 0
  }
}

// Organizers: re-fetch every existing bulk submission's counts. Each user
// costs a contribution-history walk, so this can take a few seconds.
// The server sweeps every participant in one request and answers only at
// the end, so there is no honest "x of N" to show mid-flight — the UI runs
// an indeterminate animation rather than inventing a count.
const recalcBusy = ref(false)
async function recalculateAll () {
  recalcBusy.value = true
  error.value = ''
  notice.value = ''
  try {
    const r = await api.recalculateAllBulkWikidata(props.campaign.slug)
    const d = r.data || {}
    notice.value = `Recalculated ${d.refreshed || 0} of ${d.total || 0}` +
      // Skipped rows keep their existing counts — say what to do about them.
      (d.skipped
        ? `, ${d.skipped} over ${d.cap} edits left unchanged (recalculate `
          + 'those individually)'
        : '') +
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
      <!-- "Recalculate all" runs against the lower sweep cap by design, so
           it never touches these rows. Say so, rather than leaving an
           organizer to re-run it and wonder why nothing changes. -->
      <p v-if="isOrganizer && stuckRows.length"
         class="text-xs text-amber-700 dark:text-amber-400 mb-2">
        {{ stuckRows.length }} participant(s) have more edits than the
        campaign-wide limit and are skipped by "Recalculate all" — use
        Recalculate on each of those rows to score them individually.
      </p>
      <!-- The individual limit is supposed to be the generous one. When a
           campaign carries an old stored value it can end up at or below
           the sweep limit, and then no amount of recalculating helps. -->
      <p v-if="isOrganizer && capsLookWrong"
         class="text-xs rounded-lg border border-amber-300 dark:border-amber-800
                bg-amber-50 dark:bg-amber-950/40 p-3 mb-2
                text-amber-900 dark:text-amber-300">
        This campaign limits a single recalculation to
        <strong>{{ autoCap }}</strong> edits, which is not above the
        campaign-wide limit of <strong>{{ sweepCap }}</strong> — so a
        participant with more edits than that can never be scored
        automatically. These are stored campaign settings and override the
        defaults: raise "Max Wikidata edits for automatic scoring" under
        Participation in the campaign settings.
      </p>
      <!-- Indeterminate: the sweep answers only when every participant is
           done, so there is no real progress figure to show. The moving
           bar is there to say the request is still running. -->
      <div v-if="recalcBusy" class="mb-3" aria-busy="true">
        <p class="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-300 mb-1.5">
          <svg class="w-3.5 h-3.5 animate-spin shrink-0" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Fetching each participant's Wikidata history — this can take a
          few seconds.
        </p>
        <div class="h-1.5 w-full rounded-full overflow-hidden
                    bg-neutral-200 dark:bg-neutral-800">
          <div class="h-full w-2/5 rounded-full bg-blue-600 dark:bg-blue-500
                      indeterminate-bar"></div>
        </div>
      </div>
      <p v-if="!bulkSubs.length" class="text-sm text-neutral-600 dark:text-neutral-300">
        No Wikidata bulk submissions yet.
      </p>
      <cdx-table v-else caption="Wikidata bulk submissions" :hide-caption="true"
                 :columns="columns" :data="rows">
        <template #item-username="{ item, row }">
          <button type="button" class="font-medium text-link-700 dark:text-link-400 hover:underline"
                  @click="emit('show-details', row.user)">{{ item }}</button>
          <!-- The row was last counted against a cap it exceeded. Since the
               cap was raised, Recalculate usually scores it now — say that
               rather than "needs manual scoring", which sent organizers off
               to enter points by hand for work the tool can count. -->
          <!-- Name the limit in the badge itself. A campaign saved before
               the limit was raised keeps its old value as a stored
               override, which silently beats the new default — seeing
               "over 50" rather than "over 5000" is what identifies that. -->
          <span v-if="row.over_limit"
                class="badge ml-2 bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300"
                title="Recalculate to score this against the current limit.
 If the limit shown is lower than expected, this campaign stores its own
 value for it — change it in the campaign settings.">
            over {{ row.limit ?? '?' }} edits — not counted
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
          <div class="flex items-center justify-end gap-1 whitespace-nowrap">
            <cdx-button v-if="isOrganizer" weight="quiet" size="small"
                        :disabled="recalcOne === row.id || recalcBusy"
                        title="Refetch just this participant's Wikidata history"
                        @click="recalculate(row.id, row.username)">
              {{ recalcOne === row.id ? 'Recalculating…' : 'Recalculate' }}
            </cdx-button>
            <cdx-button v-if="canRemove(row)" weight="quiet" action="destructive"
                        size="small" :disabled="removing === row.id"
                        :title="row.user.username === currentUsername
                          ? 'Withdraw your Wikidata edits submission'
                          : 'Delete this participant\'s bulk submission'"
                        @click="remove(row)">
              {{ removing === row.id
                ? '…'
                : (row.user.username === currentUsername ? 'Withdraw' : 'Delete') }}
            </cdx-button>
          </div>
        </template>
      </cdx-table>
    </div>
  </div>
</template>
