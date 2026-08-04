<script setup>
import { computed, ref, watch } from 'vue'
import { CdxButton } from '@wikimedia/codex'
import api from '../../api'
import ClaimEditor from '../ClaimEditor.vue'
import ReviewForm from '../ReviewForm.vue'
import SubmissionPreview from '../SubmissionPreview.vue'

const props = defineProps({
  campaign: { type: Object, required: true },
  submissions: { type: Array, required: true },
  // True while the list is still in flight: the page now paints before it
  // arrives, and an empty list mid-flight is not "no submissions yet".
  loading: { type: Boolean, default: false },
  isLoggedIn: { type: Boolean, required: true },
  currentUsername: { type: String, default: '' },
  isOrganizer: { type: Boolean, required: true },
  isJury: { type: Boolean, required: true },
  selfMode: { type: Boolean, required: true },
  criteria: { type: Array, required: true },
  pendingAction: { type: String, required: true }
})
const emit = defineEmits(['refresh', 'withdraw', 'moderate', 'override', 'recalculate', 'save-review', 'save-claims', 'moderate-claim'])

// Wikidata items not on the campaign's suggested list are still accepted
// (a related-but-unlisted item can be a legitimate contribution) — just
// flagged so an organizer notices and reviews it manually.
const suggestedQids = computed(() =>
  new Set((props.campaign.suggested_items || []).map(i => i.qid.toUpperCase())))
const needsListReview = (s) =>
  s.kind === 'wikidata_item' && suggestedQids.value.size > 0
  && !suggestedQids.value.has(s.title.toUpperCase())

const onlyMine = ref(false)
const filterKind = ref('')
// Bulk kinds are included so a "Wikidata edits" submission can actually be
// found in this list — the old "Wikidata only" checkbox matched
// wikidata_item alone and hid them.
// Bulk kinds are deliberately absent: they are shown on their own tab, so
// this list never contains one to filter to.
const KIND_FILTERS = [
  ['article', 'Articles'],
  ['wikidata_item', 'Wikidata items'],
  ['commons_file', 'Commons files']
]
const expanded = ref(null)
// Article details (created/updated dates + editors, bytes, words) for the
// expanded submission card — fetched from the wiki on demand, once per
// submission, and cached: 'loading' | 'error' | the details payload.
const submissionDetails = ref({})
async function toggleExpanded (s) {
  expanded.value = expanded.value === s.id ? null : s.id
  if (expanded.value !== s.id || submissionDetails.value[s.id]) return
  submissionDetails.value = { ...submissionDetails.value, [s.id]: 'loading' }
  try {
    const { data } = await api.submissionDetails(s.id)
    submissionDetails.value = { ...submissionDetails.value, [s.id]: data || 'missing' }
  } catch (e) {
    submissionDetails.value = { ...submissionDetails.value, [s.id]: 'error' }
  }
}
// Descriptive long-form date, e.g. "21 July 2026, 10:31 pm".
const fmtDateLong = (iso) => iso ? new Date(iso).toLocaleString('en-GB', {
  day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: '2-digit'
}) : '—'

// English name for non-English submissions (Wikidata item labels, and
// the connected item's English sitelink title for non-English
// articles), shown in brackets next to the native title. Fetched once
// per set of submission ids seen so far — an accept/reject/refresh
// swaps in a new submissions array without adding new ids, and must not
// re-trigger this (otherwise every moderation action pays for a wiki
// round trip it doesn't need).
const englishNames = ref({})
const knownSubmissionIds = ref(new Set())
watch(() => props.submissions, async (subs) => {
  const ids = subs.map(s => s.id)
  if (!ids.length || ids.every(id => knownSubmissionIds.value.has(id))) return
  knownSubmissionIds.value = new Set(ids)
  try {
    const { data } = await api.submissionEnglishNames(props.campaign.slug)
    englishNames.value = data
  } catch (e) { /* best-effort: the native title alone is still useful */ }
}, { immediate: true })
const englishName = (s) => {
  const entry = englishNames.value[s.id]
  return entry?.label_en || entry?.title_en || ''
}

// Preview popup: rendered lead section for an article, item data for a
// Wikidata item.
const previewSubmission = ref(null)

// Bulk submissions are a per-participant summary of a whole campaign
// window, not a page anyone can open, review or preview — they live on the
// Wikidata bulk tab, which shows their counts properly. Listing them here
// too put rows in the list that most of the row actions do not apply to.
// Every filter, count and dropdown below derives from this, so they all
// describe the same set of rows the list actually shows.
const BULK_KINDS = ['wikidata_edits', 'commons_edits']
const pageSubmissions = computed(() =>
  props.submissions.filter(s => !BULK_KINDS.includes(s.kind)))

// Coordinators can narrow the submission list to one participant.
const filterUser = ref('')
const submitterNames = computed(() =>
  [...new Set(pageSubmissions.value.map(s => s.user.username))]
    .sort((a, b) => a.localeCompare(b)))

// Language filter: the Wikipedia subdomain prefix, only meaningful for
// article submissions — only shown when the campaign actually spans more
// than one language.
const submissionLang = (s) => s.kind === 'article' ? s.wiki_domain.split('.')[0] : ''
const filterLang = ref('')
const availableLangs = computed(() =>
  [...new Set(pageSubmissions.value.map(submissionLang).filter(Boolean))].sort())

// Review-state filter, for organizers and jurors working through a
// backlog. "Awaiting my review" is per-juror; the other two are
// campaign-wide. Reviews and moderation status are independent: a
// submission can carry reviews and still be awaiting an accept/reject.
const REVIEW_FILTERS = [
  ['awaiting_me', 'Awaiting my review'],
  ['unreviewed', 'Not reviewed by anyone'],
  ['not_accepted', 'Not accepted yet'],
  ['rejected', 'Rejected']
]
const filterReview = ref('')
const reviewedByMe = (s) =>
  s.reviews.some(r => r.reviewer.username === props.currentUsername)
const REVIEW_TESTS = {
  // Own submissions are never reviewable by you, and a rejected one no
  // longer needs a decision — both would otherwise sit in your queue
  // forever as work you cannot clear.
  awaiting_me: (s, me) =>
    s.user.username !== me && s.status !== 'rejected' && !reviewedByMe(s),
  unreviewed: (s) => s.status !== 'rejected' && !s.reviews.length,
  not_accepted: (s) => s.status === 'submitted',
  rejected: (s) => s.status === 'rejected'
}

const shownSubmissions = computed(() => {
  let list = pageSubmissions.value
  if (onlyMine.value) list = list.filter(s => s.user.username === props.currentUsername)
  if (filterUser.value) list = list.filter(s => s.user.username === filterUser.value)
  if (filterLang.value) list = list.filter(s => submissionLang(s) === filterLang.value)
  if (filterKind.value) list = list.filter(s => s.kind === filterKind.value)
  const test = REVIEW_TESTS[filterReview.value]
  if (test) list = list.filter(s => test(s, props.currentUsername))
  return list
})

// Rendering every match is what actually hurts on a large campaign: a
// thousand-submission list is a thousand expandable cards in the DOM. The
// filters, counts and dropdowns above deliberately still run over the whole
// list — paginating the data instead of the rendering would make them
// describe only the current page.
const PAGE_SIZE = 50
const page = ref(1)
const pageCount = computed(() =>
  Math.max(1, Math.ceil(shownSubmissions.value.length / PAGE_SIZE)))
// Any filter change resets to the first page; without this, narrowing a
// filter while on page 7 shows an empty list. Watching the filter values
// rather than the computed list: the list is a fresh array on every
// recompute, so watching it would also reset the page on an unrelated
// refresh (accepting a submission, saving a review).
watch([onlyMine, filterUser, filterLang, filterKind, filterReview],
      () => { page.value = 1 })
// A refresh that shrinks the list can strand the reader past the end.
watch(pageCount, (n) => { if (page.value > n) page.value = n })
const pagedSubmissions = computed(() => {
  if (juryTable.value) return shownSubmissions.value   // grouped by user
  const start = (page.value - 1) * PAGE_SIZE
  return shownSubmissions.value.slice(start, start + PAGE_SIZE)
})
const pageFrom = computed(() =>
  shownSubmissions.value.length ? (page.value - 1) * PAGE_SIZE + 1 : 0)
const pageTo = computed(() =>
  Math.min(page.value * PAGE_SIZE, shownSubmissions.value.length))
function goToPage (n) {
  page.value = Math.min(Math.max(1, n), pageCount.value)
}

// Per-type counts, so an empty type is visibly empty rather than selectable.
const kindCounts = computed(() => {
  const counts = {}
  for (const s of pageSubmissions.value) counts[s.kind] = (counts[s.kind] || 0) + 1
  return counts
})

// Counts for the filter dropdown, so the size of each backlog is visible
// without having to select it first.
const reviewCounts = computed(() => Object.fromEntries(
  Object.entries(REVIEW_TESTS).map(([key, test]) => [
    key, pageSubmissions.value.filter(s => test(s, props.currentUsername)).length
  ])))

// Jury mode gets a Fountain-style table grouped by participant; self /
// hybrid keep the flat expandable list (one pseudo-group without header).
const juryTable = computed(() => props.campaign?.scoring_mode === 'jury')
const expandedUsers = ref([])
const isUserExpanded = (name) => expandedUsers.value.includes(name)
function toggleUser (name) {
  expandedUsers.value = isUserExpanded(name)
    ? expandedUsers.value.filter(n => n !== name)
    : [...expandedUsers.value, name]
}
watch(filterUser, (name) => {
  if (name && !isUserExpanded(name)) expandedUsers.value.push(name)
})
const submissionGroups = computed(() => {
  if (!juryTable.value) return [{ user: null, subs: pagedSubmissions.value }]
  const map = new Map()
  for (const s of shownSubmissions.value) {
    const g = map.get(s.user.username)
      || { user: s.user, subs: [], points: 0, reviewed: 0 }
    g.subs.push(s)
    g.points = Math.round((g.points + s.points) * 100) / 100
    if (s.reviews.length) g.reviewed += 1
    map.set(s.user.username, g)
  }
  return [...map.values()].sort((a, b) => b.points - a.points)
})

const statusStyles = {
  draft: 'bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300',
  active: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  finished: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  archived: 'bg-neutral-200 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
}
const claimStatusStyles = {
  claimed: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300',
  verified: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  adjusted: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
}
function ruleLabel (id) {
  return props.campaign?.rules.find(r => r.id === id)?.label || `rule ${id}`
}

// Tracks which per-submission action button is mid-flight, e.g.
// "42:refresh", so only that button shows a spinner and disables itself.
const isPending = (s, action) => props.pendingAction === `${s.id}:${action}`
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-x-5 gap-y-2 mb-2">
      <label v-if="isLoggedIn" class="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" v-model="onlyMine" /> Show only my submissions
      </label>
      <!-- Type filter: "Wikidata only" used to be a checkbox matching just
           wikidata_item, which left bulk submissions unfindable here. -->
      <label class="flex items-center gap-2 text-sm">
        Type
        <select v-model="filterKind" class="input !w-52 !py-1">
          <option value="">All types</option>
          <option v-for="[key, label] in KIND_FILTERS" :key="key" :value="key"
                  :disabled="!kindCounts[key]">
            {{ label }} ({{ kindCounts[key] || 0 }})
          </option>
        </select>
      </label>
      <!-- coordinator filter: one participant's submissions -->
      <label v-if="isOrganizer && submitterNames.length"
             class="flex items-center gap-2 text-sm">
        Participant
        <select v-model="filterUser" class="input !w-52 !py-1">
          <option value="">All participants</option>
          <option v-for="n in submitterNames" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <!-- language filter: only worth showing once more than one language is in play -->
      <label v-if="availableLangs.length > 1" class="flex items-center gap-2 text-sm">
        Language
        <select v-model="filterLang" class="input !w-40 !py-1">
          <option value="">All languages</option>
          <option v-for="l in availableLangs" :key="l" :value="l">{{ l }}</option>
        </select>
      </label>
      <!-- review-state filter: the reviewing backlog, for whoever works it -->
      <label v-if="isOrganizer || isJury" class="flex items-center gap-2 text-sm">
        Review state
        <select v-model="filterReview" class="input !w-56 !py-1">
          <option value="">All submissions</option>
          <option v-for="[key, label] in REVIEW_FILTERS" :key="key" :value="key"
                  :disabled="!reviewCounts[key]">
            {{ label }} ({{ reviewCounts[key] }})
          </option>
        </select>
      </label>
      <span v-if="filterUser || filterLang || filterKind || filterReview"
            class="text-xs text-neutral-600 dark:text-neutral-300">
        {{ shownSubmissions.length }} of {{ pageSubmissions.length }} submissions
      </span>
    </div>

    <p v-if="loading && !pageSubmissions.length"
       class="text-neutral-600 dark:text-neutral-300">
      Loading submissions…
    </p>
    <p v-else-if="!shownSubmissions.length" class="text-neutral-600 dark:text-neutral-300">
      {{ pageSubmissions.length ? 'No submissions match these filters.' : 'No submissions yet.' }}
    </p>

    <!-- jury mode: table header -->
    <div v-if="juryTable && shownSubmissions.length"
         class="flex items-center gap-3 px-3 pb-1 text-xs font-semibold uppercase tracking-wide
                text-neutral-500 dark:text-neutral-400">
      <span class="w-4"></span>
      <span>User</span>
      <span class="flex-1"></span>
      <span>Articles</span>
      <span class="w-20 text-right">Points</span>
    </div>

    <div v-for="g in submissionGroups" :key="g.user?.username || 'flat'">
      <!-- jury mode: one row per participant, expandable -->
      <button v-if="g.user" type="button"
              class="card w-full flex items-center gap-3 px-3 py-2 mb-2 text-left cursor-pointer
                     hover:border-blue-400 dark:hover:border-blue-600 transition-colors"
              @click="toggleUser(g.user.username)">
        <svg class="w-4 h-4 shrink-0 transition-transform text-neutral-500"
             :class="isUserExpanded(g.user.username) && 'rotate-90'"
             viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 6 6 6-6 6" />
        </svg>
        <span class="font-medium text-blue-700 dark:text-blue-400">{{ g.user.username }}</span>
        <span class="text-xs text-neutral-500 dark:text-neutral-400">
          {{ g.reviewed }}/{{ g.subs.length }} reviewed
        </span>
        <span class="flex-1"></span>
        <span class="text-sm tabular-nums">{{ g.subs.length }}</span>
        <span class="font-bold tabular-nums w-20 text-right">{{ g.points }}</span>
      </button>

      <div v-if="!g.user || isUserExpanded(g.user.username)" :class="g.user && 'pl-6 mb-1'">
        <div v-for="s in g.subs" :key="s.id" class="card mb-2">
      <div class="p-3 flex flex-wrap items-center gap-3 cursor-pointer"
           @click="toggleExpanded(s)">
        <div class="flex-1 min-w-40">
          <a :href="s.url" target="_blank" class="font-medium text-link-700 dark:text-link-400 hover:underline"
             @click.stop>{{ s.title }}</a>
          <span v-if="englishName(s)" class="text-sm text-neutral-500 dark:text-neutral-400">
            ({{ englishName(s) }})</span>
          <div class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
            by {{ s.user.username }} · {{ new Date(s.submitted_at).toLocaleDateString() }}
            <template v-if="campaign.settings.multi_language && s.kind === 'article'">
              · {{ s.wiki_domain.split('.')[0] }}
            </template>
            <template v-if="s.kind === 'wikidata_item'"> · Wikidata</template>
            <template v-if="s.kind === 'commons_file'"> · Commons</template>
            <template v-if="s.bytes_added"> · +{{ s.bytes_added.toLocaleString() }} bytes</template>
            <template v-if="s.kind === 'wikidata_edits' && s.metrics && !s.metrics.over_limit">
              · {{ s.metrics.statements }} statements
              · {{ s.metrics.terms }} labels/descriptions/aliases
              · {{ (s.metrics.eligible_qids || []).length }} of {{ s.metrics.edited_qids }} items eligible
            </template>
            <template v-if="s.kind === 'commons_edits' && s.metrics && !s.metrics.over_limit">
              · {{ s.metrics.uploads }} uploads · {{ s.metrics.depicts }} depicts
            </template>
            <span v-if="s.metrics && s.metrics.over_limit"
                  class="text-amber-700 dark:text-amber-400 font-medium">
              · over {{ s.metrics.limit }} edits — needs manual scoring
            </span>
          </div>
          <p v-if="s.status === 'rejected' && s.moderation_note"
             class="text-xs text-red-700 dark:text-red-400 mt-1">
            Reason: {{ s.moderation_note }}
          </p>
          <p v-if="needsListReview(s)" class="text-xs text-amber-700 dark:text-amber-400 mt-1">
            Not on the suggested items list — please review manually.
          </p>
        </div>
        <span v-if="needsListReview(s)"
              class="badge bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
              title="This Wikidata item isn't on the campaign's suggested list">
          needs review
        </span>
        <span v-if="s.is_new_page" class="badge bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
          new article
        </span>
        <span v-if="s.status !== 'submitted'" class="badge" :class="statusStyles[s.status === 'accepted' ? 'active' : 'rejected']">
          {{ s.status }}
        </span>
        <span v-if="s.status !== 'rejected'" class="font-bold tabular-nums text-lg">{{ s.points }}<span class="text-xs font-normal text-neutral-600 dark:text-neutral-300"> pts</span></span>
      </div>

      <div v-if="expanded === s.id" class="border-t border-neutral-100 dark:border-neutral-800 p-3 space-y-4">
        <!-- live wiki details: created/updated dates and editors, bytes -->
        <div v-if="!['wikidata_edits', 'commons_edits'].includes(s.kind)">
          <h5 class="label">Article details</h5>
          <div v-if="submissionDetails[s.id] === 'loading'"
               class="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">
            <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Fetching details from the wiki…
          </div>
          <p v-else-if="submissionDetails[s.id] === 'error'"
             class="text-sm text-red-600 dark:text-red-400">
            Could not fetch details from the wiki.
          </p>
          <p v-else-if="submissionDetails[s.id] === 'missing'"
             class="text-sm text-neutral-600 dark:text-neutral-300">
            Not found on the wiki.
          </p>
          <div v-else-if="submissionDetails[s.id]" class="grid sm:grid-cols-2 gap-3">
            <!-- creation: words, who, when -->
            <div class="rounded-lg border border-blue-200 dark:border-blue-900
                        bg-blue-50 dark:bg-blue-950/40 p-3 grid grid-cols-3 gap-2 text-sm">
              <div v-if="submissionDetails[s.id].words != null">
                <dt class="text-xs text-blue-800 dark:text-blue-300">Words</dt>
                <dd class="tabular-nums font-semibold text-blue-900 dark:text-blue-100">
                  {{ submissionDetails[s.id].words.toLocaleString() }}
                </dd>
              </div>
              <div>
                <dt class="text-xs text-blue-800 dark:text-blue-300">Created by</dt>
                <dd class="font-semibold text-blue-900 dark:text-blue-100">
                  {{ submissionDetails[s.id].created_by || submissionDetails[s.id].uploader || '—' }}
                </dd>
              </div>
              <div class="col-span-3 sm:col-span-1">
                <dt class="text-xs text-blue-800 dark:text-blue-300">Created on</dt>
                <dd class="font-semibold text-blue-900 dark:text-blue-100">
                  {{ fmtDateLong(submissionDetails[s.id].created_at || submissionDetails[s.id].uploaded_at) }}
                </dd>
              </div>
            </div>
            <!-- latest state: total bytes, who, when -->
            <div class="rounded-lg border border-green-200 dark:border-green-900
                        bg-green-50 dark:bg-green-950/40 p-3 grid grid-cols-3 gap-2 text-sm">
              <div>
                <dt class="text-xs text-green-800 dark:text-green-300">Total bytes</dt>
                <dd class="tabular-nums font-semibold text-green-900 dark:text-green-100">
                  {{ (submissionDetails[s.id].bytes ?? submissionDetails[s.id].size)?.toLocaleString() ?? '—' }}
                </dd>
              </div>
              <div>
                <dt class="text-xs text-green-800 dark:text-green-300">Last updated by</dt>
                <dd class="font-semibold text-green-900 dark:text-green-100">
                  {{ submissionDetails[s.id].last_updated_by || '—' }}
                </dd>
              </div>
              <div class="col-span-3 sm:col-span-1">
                <dt class="text-xs text-green-800 dark:text-green-300">Updated on</dt>
                <dd class="font-semibold text-green-900 dark:text-green-100">
                  {{ fmtDateLong(submissionDetails[s.id].last_updated) }}
                </dd>
              </div>
            </div>
          </div>
        </div>

        <!-- bulk submission over the auto-scoring cap: manual points only -->
        <p v-if="s.metrics && s.metrics.over_limit"
           class="text-sm rounded-lg px-3 py-2 bg-amber-50 text-amber-800
                  dark:bg-amber-950/50 dark:text-amber-300">
          This user made more than {{ s.metrics.limit }} edits in the campaign
          period (likely a QuickStatements / OpenRefine or mass-upload run), so
          the points cannot be calculated automatically.
          <a :href="s.url" target="_blank" class="text-link-700 dark:text-link-400 underline">Review the
          contributions ↗</a>, decide whether these edits count, and enter the
          points with <b>Override points</b>.
        </p>

        <!-- points breakdown -->
        <div v-if="s.breakdown.length">
          <h5 class="label">Points breakdown</h5>
          <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div v-for="(line, i) in s.breakdown" :key="i"
                 class="rounded-lg border border-violet-200 dark:border-violet-900
                        bg-violet-50 dark:bg-violet-950/40 p-3 flex items-center justify-between gap-3">
              <div class="min-w-0">
                <div class="text-sm font-medium text-violet-900 dark:text-violet-100 truncate">{{ line.label }}</div>
                <div class="text-xs text-violet-700 dark:text-violet-400">
                  {{ line.source }}<template v-if="line.status"> · {{ line.status }}</template>
                </div>
              </div>
              <div class="text-lg font-extrabold tabular-nums text-violet-900 dark:text-violet-100 shrink-0">
                {{ line.points }}
              </div>
            </div>
          </div>
        </div>

        <!-- reviews -->
        <div v-if="s.reviews.length">
          <h5 class="label">Reviews</h5>
          <div v-for="r in s.reviews" :key="r.id" class="text-sm py-1 flex gap-2 items-baseline">
            <b>{{ r.reviewer.username }}</b>
            <span class="badge" :class="claimStatusStyles[r.decision === 'accept' ? 'verified' : r.decision === 'reject' ? 'rejected' : 'claimed']">{{ r.decision }}</span>
            <span class="tabular-nums">{{ r.total }} pts</span>
            <span class="text-neutral-600 dark:text-neutral-300">{{ r.comment }}</span>
          </div>
        </div>

        <!-- claims (self mode) -->
        <div v-if="selfMode && s.claims.length">
          <h5 class="label">Claims</h5>
          <div v-for="c in s.claims" :key="c.id" class="text-sm py-1 flex flex-wrap gap-2 items-center">
            <span>{{ ruleLabel(c.rule_id) }} × {{ c.quantity }}</span>
            <span class="badge" :class="claimStatusStyles[c.status]">{{ c.status }}</span>
            <span class="tabular-nums">{{ c.points_final ?? c.points_claimed }} pts</span>
            <a v-if="c.evidence_url" :href="c.evidence_url" target="_blank"
               class="text-link-700 dark:text-link-400 text-xs hover:underline">evidence</a>
            <template v-if="isJury && campaign.status !== 'archived'">
              <button class="btn !py-0.5 !px-2 text-xs" @click="emit('moderate-claim', c, 'verified')">Verify</button>
              <button class="btn !py-0.5 !px-2 text-xs" @click="emit('moderate-claim', c, 'adjusted')">Adjust</button>
              <button class="btn-danger !py-0.5 !px-2 text-xs" @click="emit('moderate-claim', c, 'rejected')">Reject</button>
            </template>
          </div>
        </div>

        <!-- claim editor for the owner -->
        <div v-if="selfMode && currentUsername === s.user.username && campaign.status !== 'archived'">
          <h5 class="label">Claim your points</h5>
          <ClaimEditor :rules="campaign.rules" :submission="s" @save="claims => emit('save-claims', s, claims)" />
        </div>

        <!-- review form for jurors -->
        <div v-if="isJury && campaign.scoring_mode !== 'self' && currentUsername !== s.user.username && campaign.status !== 'archived'">
          <h5 class="label">Your review</h5>
          <ReviewForm :criteria="criteria"
                      :existing="s.reviews.find(r => r.reviewer.username === currentUsername)"
                      @save="review => emit('save-review', s, review)" />
        </div>

        <!-- actions -->
        <div class="flex flex-wrap gap-2 pt-1">
          <button v-if="['article', 'wikidata_item'].includes(s.kind)"
                  class="btn" @click.stop="previewSubmission = s">
            Preview
          </button>
          <button class="btn" :disabled="isPending(s, 'refresh')" @click="emit('refresh', s)">
            <svg v-if="isPending(s, 'refresh')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Refresh wiki data
          </button>
          <button v-if="currentUsername === s.user.username && campaign.status === 'active'"
                  class="btn-danger" :disabled="isPending(s, 'withdraw')" @click="emit('withdraw', s)">
            <svg v-if="isPending(s, 'withdraw')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Withdraw
          </button>
          <template v-if="isOrganizer">
            <button class="btn-success" :disabled="isPending(s, 'accepted')" @click="emit('moderate', s, 'accepted')">
              <svg v-if="isPending(s, 'accepted')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Accept
            </button>
            <button class="btn-danger" :disabled="isPending(s, 'rejected')" @click="emit('moderate', s, 'rejected')">
              <svg v-if="isPending(s, 'rejected')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Reject
            </button>
            <button class="btn-warning" :disabled="isPending(s, 'override')" @click="emit('override', s)">
              <svg v-if="isPending(s, 'override')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Override points
            </button>
          </template>
          <button v-if="isOrganizer || currentUsername === s.user.username"
                  class="btn" :disabled="isPending(s, 'recalculate')"
                  :title="isOrganizer
                    ? 'Refetch wiki data and rescore from the campaign rules, clearing any override'
                    : 'Refetch wiki data and rescore from the campaign rules (an existing organizer override, if any, is kept)'"
                  @click="emit('recalculate', s)">
            <svg v-if="isPending(s, 'recalculate')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Recalculate points
          </button>
        </div>
      </div>
    </div>
      </div>
    </div>

    <!-- Pager: flat list only. Jury mode groups by participant, which is
         already bounded by the number of people in the campaign. -->
    <div v-if="!juryTable && pageCount > 1"
         class="flex flex-wrap items-center justify-between gap-3 mt-4 pt-3
                border-t border-neutral-200 dark:border-neutral-800">
      <span class="text-xs text-neutral-600 dark:text-neutral-300 tabular-nums">
        Showing {{ pageFrom }}–{{ pageTo }} of {{ shownSubmissions.length }}
      </span>
      <div class="flex items-center gap-1">
        <cdx-button weight="quiet" size="small" :disabled="page === 1"
                    @click="goToPage(page - 1)">← Previous</cdx-button>
        <span class="text-sm px-2 tabular-nums">
          Page {{ page }} of {{ pageCount }}
        </span>
        <cdx-button weight="quiet" size="small" :disabled="page === pageCount"
                    @click="goToPage(page + 1)">Next →</cdx-button>
      </div>
    </div>

    <SubmissionPreview v-if="previewSubmission" :submission="previewSubmission"
                        @close="previewSubmission = null" />
  </div>
</template>
