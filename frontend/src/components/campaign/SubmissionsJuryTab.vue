<script setup>
// Jury-mode Submissions tab: a Fountain-style table grouped by
// participant. The group rows (submissions / reviewed / points per user)
// come from the leaderboard endpoint — a single grouped SQL query the
// server computes over the cached points — and expanding a participant
// fetches just that user's submissions. Nothing here ever loads the
// whole campaign.
//
// If the leaderboard is hidden from this viewer, the tab falls back to
// the flat paged list rather than showing nothing.
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '../../api'
import SubmissionCard from './SubmissionCard.vue'
import SubmissionsListTab from './SubmissionsListTab.vue'

const props = defineProps({
  campaign: { type: Object, required: true },
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

const fallback = ref(false)
const rows = ref([])
const loading = ref(true)
const onlyMine = ref(false)
const filterUser = ref('')
const filterReview = ref('')
const REVIEW_FILTERS = [
  ['awaiting_me', 'Awaiting my review'],
  ['unreviewed', 'Not reviewed by anyone'],
  ['not_accepted', 'Not accepted yet'],
  ['rejected', 'Rejected']
]
const facets = ref(null)

async function fetchRows () {
  loading.value = true
  try {
    rows.value = (await api.leaderboard(props.campaign.slug)).data
    // Facet counts for the dropdowns arrive with a minimal page fetch —
    // the grouped view itself needs no rows.
    const { data } = await api.listSubmissions(props.campaign.slug,
      { per_page: 1, exclude_bulk: 1, facets: 1 })
    facets.value = data.facets
  } catch (e) {
    // Leaderboard not visible to this viewer — flat list instead.
    fallback.value = true
  } finally {
    loading.value = false
  }
}

const expandedUsers = ref([])
const isUserExpanded = (name) => expandedUsers.value.includes(name)
// username -> { loading, subs } for expanded groups.
const userSubs = reactive({})
async function loadUserSubs (name) {
  userSubs[name] = { loading: true, subs: userSubs[name]?.subs || [] }
  try {
    const params = { user: name, exclude_bulk: 1, per_page: 500 }
    if (filterReview.value) params.review = filterReview.value
    const { data } = await api.listSubmissions(props.campaign.slug, params)
    userSubs[name] = { loading: false, subs: data.items }
  } catch (e) {
    userSubs[name] = { loading: false, subs: [] }
  }
}
function toggleUser (name) {
  if (isUserExpanded(name)) {
    expandedUsers.value = expandedUsers.value.filter(n => n !== name)
  } else {
    expandedUsers.value = [...expandedUsers.value, name]
    loadUserSubs(name)
  }
}
watch(filterUser, (name) => {
  if (name && !isUserExpanded(name)) toggleUser(name)
})
watch(filterReview, () => {
  for (const name of expandedUsers.value) loadUserSubs(name)
})

function refreshAll () {
  fetchRows()
  for (const name of expandedUsers.value) loadUserSubs(name)
}
watch(() => props.refreshTick, refreshAll)
onMounted(fetchRows)

const groups = computed(() => {
  let list = rows.value
  if (filterUser.value) list = list.filter(r => r.user.username === filterUser.value)
  if (onlyMine.value) list = list.filter(r => r.user.username === props.currentUsername)
  return list.map(r => ({
    user: r.user,
    count: r.submission_count,
    points: r.points,
    reviewed: r.reviewed_count || 0,
    loading: userSubs[r.user.username]?.loading || false,
    subs: userSubs[r.user.username]?.subs || []
  }))
})
const participantNames = computed(() => facets.value?.participants || [])
const reviewCounts = computed(() => facets.value?.review || {})
</script>

<template>
  <!-- leaderboard hidden from this viewer: flat paged list instead -->
  <SubmissionsListTab v-if="fallback"
                      :campaign="campaign" :refresh-tick="refreshTick"
                      :is-logged-in="isLoggedIn" :current-username="currentUsername"
                      :is-organizer="isOrganizer" :is-jury="isJury"
                      :self-mode="selfMode" :criteria="criteria"
                      :pending-action="pendingAction"
                      @refresh="emit('refresh', $event)"
                      @withdraw="emit('withdraw', $event)"
                      @moderate="(s, status) => emit('moderate', s, status)"
                      @override="emit('override', $event)"
                      @recalculate="emit('recalculate', $event)"
                      @save-review="(s, review) => emit('save-review', s, review)"
                      @save-claims="(s, claims) => emit('save-claims', s, claims)"
                      @moderate-claim="(claim, status) => emit('moderate-claim', claim, status)" />

  <div v-else>
    <div class="flex flex-wrap items-center gap-x-5 gap-y-2 mb-2">
      <label v-if="isLoggedIn" class="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" v-model="onlyMine" /> Show only my submissions
      </label>
      <label v-if="isOrganizer && participantNames.length"
             class="flex items-center gap-2 text-sm">
        Participant
        <select v-model="filterUser" class="input !w-52 !py-1">
          <option value="">All participants</option>
          <option v-for="n in participantNames" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <!-- narrows the rows inside each expanded participant -->
      <label v-if="isOrganizer || isJury" class="flex items-center gap-2 text-sm">
        Review state
        <select v-model="filterReview" class="input !w-56 !py-1">
          <option value="">All submissions</option>
          <option v-for="[key, label] in REVIEW_FILTERS" :key="key" :value="key"
                  :disabled="!reviewCounts[key]">
            {{ label }} ({{ reviewCounts[key] ?? 0 }})
          </option>
        </select>
      </label>
    </div>

    <p v-if="loading && !groups.length"
       class="text-neutral-600 dark:text-neutral-300">
      Loading participants…
    </p>
    <p v-else-if="!groups.length" class="text-neutral-600 dark:text-neutral-300">
      No submissions yet.
    </p>

    <div v-if="groups.length"
         class="flex items-center gap-3 px-3 pb-1 text-xs font-semibold uppercase tracking-wide
                text-neutral-500 dark:text-neutral-400">
      <span class="w-4"></span>
      <span>User</span>
      <span class="flex-1"></span>
      <span>Articles</span>
      <span class="w-20 text-right">Points</span>
    </div>

    <div v-for="g in groups" :key="g.user.username">
      <button type="button"
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
          {{ g.reviewed }}/{{ g.count }} reviewed
        </span>
        <span class="flex-1"></span>
        <span class="text-sm tabular-nums">{{ g.count }}</span>
        <span class="font-bold tabular-nums w-20 text-right">{{ g.points }}</span>
      </button>

      <div v-if="isUserExpanded(g.user.username)" class="pl-6 mb-1">
        <p v-if="g.loading && !g.subs.length"
           class="text-sm text-neutral-600 dark:text-neutral-300 pb-2">
          Loading submissions…
        </p>
        <p v-else-if="!g.subs.length"
           class="text-sm text-neutral-600 dark:text-neutral-300 pb-2">
          {{ filterReview ? 'Nothing matches this filter for this participant.'
                          : 'No submissions.' }}
        </p>
        <SubmissionCard v-for="s in g.subs" :key="s.id"
                        :campaign="campaign" :submission="s"
                        :refresh-tick="refreshTick"
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
      </div>
    </div>
  </div>
</template>
