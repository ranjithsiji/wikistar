<script setup>
// Flat, server-paged submissions list — the Submissions tab of
// self/hybrid campaigns, and (mode="backlog") the review tab of every
// scoring mode. Jury campaigns group their Submissions tab by
// participant instead: see SubmissionsJuryTab.vue.
//
// Every filter is a server parameter: each change asks the backend for
// one page of matching rows plus campaign-wide facet counts, so the
// dropdowns describe the whole campaign while only fifty rows travel.
import { computed, onMounted, ref, watch } from 'vue'
import { CdxButton } from '@wikimedia/codex'
import api from '../../api'
import SubmissionCard from './SubmissionCard.vue'

const props = defineProps({
  campaign: { type: Object, required: true },
  // 'all' — the Submissions tab; 'backlog' — the review tab, pinned to
  // the submissions still waiting for a review (jury) or an
  // accept/reject decision (self-assessment).
  mode: { type: String, default: 'all' },
  // Bumped by the parent after any action that changes submissions.
  refreshTick: { type: Number, default: 0 },
  isLoggedIn: { type: Boolean, required: true },
  currentUsername: { type: String, default: '' },
  isOrganizer: { type: Boolean, required: true },
  isJury: { type: Boolean, required: true },
  selfMode: { type: Boolean, required: true },
  criteria: { type: Array, required: true },
  pendingAction: { type: String, required: true }
})
const emit = defineEmits(['refresh', 'withdraw', 'moderate', 'override',
                          'recalculate', 'save-review', 'save-claims',
                          'moderate-claim'])

const KIND_FILTERS = [
  ['article', 'Articles'],
  ['wikidata_item', 'Wikidata items'],
  ['commons_file', 'Commons files']
]
const REVIEW_FILTERS = [
  ['awaiting_me', 'Awaiting my review'],
  ['unreviewed', 'Not reviewed by anyone'],
  ['not_accepted', 'Not accepted yet'],
  ['rejected', 'Rejected']
]

const onlyMine = ref(false)
const filterKind = ref('')
const filterUser = ref('')
const filterLang = ref('')
const filterReview = ref('')
// The backlog pins the review filter instead of offering the dropdown.
const backlogReview = computed(() =>
  props.campaign?.scoring_mode === 'jury' ? 'unreviewed' : 'not_accepted')
const effectiveReview = computed(() =>
  props.mode === 'backlog' ? backlogReview.value : filterReview.value)

const PAGE_SIZE = 50
const items = ref([])
const total = ref(0)
const pages = ref(1)
const page = ref(1)
const facets = ref(null)
const loading = ref(true)

async function fetchPage () {
  loading.value = true
  try {
    const params = {
      page: page.value, per_page: PAGE_SIZE, exclude_bulk: 1, facets: 1
    }
    if (onlyMine.value) params.mine = 1
    if (filterKind.value) params.kind = filterKind.value
    if (filterUser.value) params.user = filterUser.value
    if (filterLang.value) params.language = filterLang.value
    if (effectiveReview.value) params.review = effectiveReview.value
    const { data } = await api.listSubmissions(props.campaign.slug, params)
    items.value = data.items
    total.value = data.total
    pages.value = data.pages
    facets.value = data.facets
    // A refetch that shrank the list can strand the reader past the end.
    if (page.value > data.pages) page.value = data.pages
    loadEnglishNames(data.items)
  } catch (e) {
    items.value = []
    total.value = 0
    pages.value = 1
  } finally {
    loading.value = false
  }
}

watch(page, fetchPage)
// A filter change restarts from page 1; setting page fetches through its
// own watcher, so fetch directly only when already there.
watch([onlyMine, filterKind, filterUser, filterLang, filterReview], () => {
  if (page.value !== 1) page.value = 1
  else fetchPage()
})
watch(() => props.refreshTick, fetchPage)
onMounted(fetchPage)

const kindCounts = computed(() => facets.value?.kinds || {})
const reviewCounts = computed(() => facets.value?.review || {})
const submitterNames = computed(() => facets.value?.participants || [])
const availableLangs = computed(() => facets.value?.languages || [])
// Whole campaign vs current filter — for the "no submissions yet" vs
// "nothing matches" distinction and the filter summary line.
const overallTotal = computed(() =>
  facets.value
    ? Object.values(facets.value.kinds).reduce((a, b) => a + b, 0)
    : 0)
const hasFilters = computed(() =>
  Boolean(onlyMine.value || filterKind.value || filterUser.value
          || filterLang.value || filterReview.value))

const pageFrom = computed(() =>
  total.value ? (page.value - 1) * PAGE_SIZE + 1 : 0)
const pageTo = computed(() =>
  Math.min(page.value * PAGE_SIZE, total.value))
function goToPage (n) {
  page.value = Math.min(Math.max(1, n), pages.value)
}

// English name for non-English submissions, shown in brackets next to
// the native title. Requested only for rows this tab has shown, once per
// id — refetches after moderation must not pay for extra wiki trips.
const englishNames = ref({})
const englishNamesAsked = new Set()
async function loadEnglishNames (subs) {
  const ids = subs.map(s => s.id).filter(id => !englishNamesAsked.has(id))
  if (!ids.length) return
  ids.forEach(id => englishNamesAsked.add(id))
  try {
    const { data } = await api.submissionEnglishNames(props.campaign.slug, ids)
    englishNames.value = { ...englishNames.value, ...data }
  } catch (e) { /* best-effort: the native title alone is still useful */ }
}
const englishName = (s) => {
  const entry = englishNames.value[s.id]
  return entry?.label_en || entry?.title_en || ''
}
</script>

<template>
  <div>
    <p v-if="mode === 'backlog'" class="text-sm text-neutral-600 dark:text-neutral-300 mb-3">
      <template v-if="loading && !items.length">Loading the backlog…</template>
      <template v-else-if="total">
        {{ total }}
        {{ campaign.scoring_mode === 'jury'
          ? 'submission(s) no juror has reviewed yet.'
          : 'submission(s) waiting to be accepted or rejected.' }}
      </template>
      <template v-else>
        Nothing is waiting — every submission has been
        {{ campaign.scoring_mode === 'jury' ? 'reviewed' : 'moderated' }}.
      </template>
    </p>

    <div class="flex flex-wrap items-center gap-x-5 gap-y-2 mb-2">
      <label v-if="isLoggedIn && mode !== 'backlog'" class="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" v-model="onlyMine" /> Show only my submissions
      </label>
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
      <!-- review-state filter: the reviewing backlog, for whoever works it.
           The backlog tab pins this filter, so no dropdown there. -->
      <label v-if="(isOrganizer || isJury) && mode !== 'backlog'"
             class="flex items-center gap-2 text-sm">
        Review state
        <select v-model="filterReview" class="input !w-56 !py-1">
          <option value="">All submissions</option>
          <option v-for="[key, label] in REVIEW_FILTERS" :key="key" :value="key"
                  :disabled="!reviewCounts[key]">
            {{ label }} ({{ reviewCounts[key] ?? 0 }})
          </option>
        </select>
      </label>
      <span v-if="hasFilters"
            class="text-xs text-neutral-600 dark:text-neutral-300">
        {{ total }} of {{ overallTotal }} submissions
      </span>
    </div>

    <p v-if="loading && !items.length"
       class="text-neutral-600 dark:text-neutral-300">
      Loading submissions…
    </p>
    <p v-else-if="!items.length" class="text-neutral-600 dark:text-neutral-300">
      {{ hasFilters && overallTotal ? 'No submissions match these filters.' : 'No submissions yet.' }}
    </p>

    <SubmissionCard v-for="s in items" :key="s.id"
                    :campaign="campaign" :submission="s"
                    :english-name="englishName(s)" :refresh-tick="refreshTick"
                    :current-username="currentUsername"
                    :is-organizer="isOrganizer" :is-jury="isJury"
                    :self-mode="selfMode" :criteria="criteria"
                    :pending-action="pendingAction"
                    @refresh="emit('refresh', $event)"
                    @withdraw="emit('withdraw', $event)"
                    @moderate="(s2, status) => emit('moderate', s2, status)"
                    @override="emit('override', $event)"
                    @recalculate="emit('recalculate', $event)"
                    @save-review="(s2, review) => emit('save-review', s2, review)"
                    @save-claims="(s2, claims) => emit('save-claims', s2, claims)"
                    @moderate-claim="(claim, status) => emit('moderate-claim', claim, status)" />

    <div v-if="pages > 1"
         class="flex flex-wrap items-center justify-between gap-3 mt-4 pt-3
                border-t border-neutral-200 dark:border-neutral-800">
      <span class="text-xs text-neutral-600 dark:text-neutral-300 tabular-nums">
        Showing {{ pageFrom }}–{{ pageTo }} of {{ total }}
      </span>
      <div class="flex items-center gap-1">
        <cdx-button weight="quiet" size="small" :disabled="page === 1 || loading"
                    @click="goToPage(page - 1)">← Previous</cdx-button>
        <span class="text-sm px-2 tabular-nums">
          Page {{ page }} of {{ pages }}
        </span>
        <cdx-button weight="quiet" size="small" :disabled="page === pages || loading"
                    @click="goToPage(page + 1)">Next →</cdx-button>
      </div>
    </div>
  </div>
</template>
