<script setup>
import { computed, ref, watch } from 'vue'
import api from '../../api'
import ClaimEditor from '../ClaimEditor.vue'
import ReviewForm from '../ReviewForm.vue'

const props = defineProps({
  campaign: { type: Object, required: true },
  submissions: { type: Array, required: true },
  isLoggedIn: { type: Boolean, required: true },
  currentUsername: { type: String, default: '' },
  isOrganizer: { type: Boolean, required: true },
  isJury: { type: Boolean, required: true },
  selfMode: { type: Boolean, required: true },
  criteria: { type: Array, required: true },
  pendingAction: { type: String, required: true }
})
const emit = defineEmits(['refresh', 'withdraw', 'moderate', 'override', 'recalculate', 'save-review', 'save-claims', 'moderate-claim'])

const onlyMine = ref(false)
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

// Coordinators can narrow the submission list to one participant.
const filterUser = ref('')
const submitterNames = computed(() =>
  [...new Set(props.submissions.map(s => s.user.username))]
    .sort((a, b) => a.localeCompare(b)))

// Language filter: the Wikipedia subdomain prefix, only meaningful for
// article submissions — only shown when the campaign actually spans more
// than one language.
const submissionLang = (s) => s.kind === 'article' ? s.wiki_domain.split('.')[0] : ''
const filterLang = ref('')
const availableLangs = computed(() =>
  [...new Set(props.submissions.map(submissionLang).filter(Boolean))].sort())

const shownSubmissions = computed(() => {
  let list = props.submissions
  if (onlyMine.value) list = list.filter(s => s.user.username === props.currentUsername)
  if (filterUser.value) list = list.filter(s => s.user.username === filterUser.value)
  if (filterLang.value) list = list.filter(s => submissionLang(s) === filterLang.value)
  return list
})

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
  if (!juryTable.value) return [{ user: null, subs: shownSubmissions.value }]
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
      <span v-if="filterUser || filterLang" class="text-xs text-neutral-600 dark:text-neutral-300">
        {{ shownSubmissions.length }} of {{ submissions.length }} submissions
      </span>
    </div>

    <p v-if="!shownSubmissions.length" class="text-neutral-600 dark:text-neutral-300">No submissions yet.</p>

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
          <a :href="s.url" target="_blank" class="font-medium text-blue-700 dark:text-blue-400 hover:underline"
             @click.stop>{{ s.title }}</a>
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
        </div>
        <span v-if="s.is_new_page" class="badge bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300">
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
          <a :href="s.url" target="_blank" class="underline">Review the
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
               class="text-blue-600 dark:text-blue-400 text-xs hover:underline">evidence</a>
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
            <button class="btn" :disabled="isPending(s, 'recalculate')"
                    title="Refetch wiki data and rescore from the campaign rules, clearing any override"
                    @click="emit('recalculate', s)">
              <svg v-if="isPending(s, 'recalculate')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Recalculate points
            </button>
          </template>
        </div>
      </div>
    </div>
      </div>
    </div>
  </div>
</template>
