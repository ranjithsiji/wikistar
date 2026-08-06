<script setup>
// One submission card, shared by the flat (self/hybrid) list, the jury
// table's expanded groups and the review backlog.
//
// The list row arrives lean from the paged endpoint: stored columns plus
// the cached points. Everything heavier — the points breakdown, reviews
// and claims — is fetched per submission when the card is expanded, and
// the live wiki facts (words, dates, editors) come from their own
// endpoint on top, so a page of fifty rows costs one SQL query however
// large the campaign is.
import { computed, ref, watch } from 'vue'
import api from '../../api'
import ClaimEditor from '../ClaimEditor.vue'
import ReviewForm from '../ReviewForm.vue'
import SubmissionPreview from '../SubmissionPreview.vue'

const props = defineProps({
  campaign: { type: Object, required: true },
  submission: { type: Object, required: true },
  englishName: { type: String, default: '' },
  // Bumped by the parent after any action that changes submissions; an
  // expanded card refetches its detail so reviews/claims stay current.
  refreshTick: { type: Number, default: 0 },
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

const s = computed(() => props.submission)

// Wikidata items not on the campaign's suggested list are still accepted
// (a related-but-unlisted item can be a legitimate contribution) — just
// flagged so an organizer notices and reviews it manually.
const suggestedQids = computed(() =>
  new Set((props.campaign.suggested_items || []).map(i => i.qid.toUpperCase())))
const needsListReview = computed(() =>
  s.value.kind === 'wikidata_item' && suggestedQids.value.size > 0
  && !suggestedQids.value.has(s.value.title.toUpperCase()))

const expanded = ref(false)

// Per-submission detail (breakdown, reviews, claims): fetched on first
// expand, refetched when the parent signals a change while expanded.
// detailVersion keys the claim editor so it re-reads fresh claims.
const detail = ref(null)
const detailState = ref('idle')      // idle | loading | ready | error
const detailVersion = ref(0)
async function loadDetail () {
  detailState.value = detail.value ? detailState.value : 'loading'
  try {
    const { data } = await api.getSubmission(s.value.id)
    detail.value = data
    detailVersion.value += 1
    detailState.value = 'ready'
  } catch (e) {
    detailState.value = 'error'
  }
}

// Live wiki facts (words, dates, editors) — fetched once per expand
// lifetime; a moderation action doesn't change them.
const wikiDetails = ref(null)        // null | 'loading' | 'error' | 'missing' | data
async function loadWikiDetails () {
  if (wikiDetails.value && wikiDetails.value !== 'error') return
  wikiDetails.value = 'loading'
  try {
    const { data } = await api.submissionDetails(s.value.id)
    wikiDetails.value = data || 'missing'
  } catch (e) {
    wikiDetails.value = 'error'
  }
}

const isBulk = computed(() =>
  ['wikidata_edits', 'commons_edits'].includes(s.value.kind))

function toggleExpanded () {
  expanded.value = !expanded.value
  if (expanded.value) {
    loadDetail()
    if (!isBulk.value) loadWikiDetails()
  }
}
watch(() => props.refreshTick, () => { if (expanded.value) loadDetail() })

// Preview popup: rendered lead section for an article, item data for a
// Wikidata item.
const showPreview = ref(false)

// Descriptive long-form date, e.g. "21 July 2026, 10:31 pm".
const fmtDateLong = (iso) => iso ? new Date(iso).toLocaleString('en-GB', {
  day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: '2-digit'
}) : '—'

const statusStyles = {
  active: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
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
const isPending = (action) => props.pendingAction === `${s.value.id}:${action}`
</script>

<template>
  <div class="card mb-2">
    <div class="p-3 flex flex-wrap items-center gap-3 cursor-pointer"
         @click="toggleExpanded">
      <div class="flex-1 min-w-40">
        <a :href="s.url" target="_blank" class="font-medium text-link-700 dark:text-link-400 hover:underline"
           @click.stop>{{ s.title }}</a>
        <span v-if="englishName" class="text-sm text-neutral-500 dark:text-neutral-400">
          ({{ englishName }})</span>
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
        <p v-if="needsListReview" class="text-xs text-amber-700 dark:text-amber-400 mt-1">
          Not on the suggested items list — please review manually.
        </p>
      </div>
      <span v-if="needsListReview"
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

    <div v-if="expanded" class="border-t border-neutral-100 dark:border-neutral-800 p-3 space-y-4">
      <!-- live wiki details: created/updated dates and editors, bytes -->
      <div v-if="!isBulk">
        <h5 class="label">Article details</h5>
        <div v-if="wikiDetails === 'loading'"
             class="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">
          <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Fetching details from the wiki…
        </div>
        <p v-else-if="wikiDetails === 'error'"
           class="text-sm text-red-600 dark:text-red-400">
          Could not fetch details from the wiki.
        </p>
        <p v-else-if="wikiDetails === 'missing'"
           class="text-sm text-neutral-600 dark:text-neutral-300">
          Not found on the wiki.
        </p>
        <div v-else-if="wikiDetails" class="grid sm:grid-cols-2 gap-3">
          <!-- creation: words, who, when -->
          <div class="rounded-lg border border-blue-200 dark:border-blue-900
                      bg-blue-50 dark:bg-blue-950/40 p-3 grid grid-cols-3 gap-2 text-sm">
            <div v-if="wikiDetails.words != null">
              <dt class="text-xs text-blue-800 dark:text-blue-300">Words</dt>
              <dd class="tabular-nums font-semibold text-blue-900 dark:text-blue-100">
                {{ wikiDetails.words.toLocaleString() }}
              </dd>
            </div>
            <div>
              <dt class="text-xs text-blue-800 dark:text-blue-300">Created by</dt>
              <dd class="font-semibold text-blue-900 dark:text-blue-100">
                {{ wikiDetails.created_by || wikiDetails.uploader || '—' }}
              </dd>
            </div>
            <div class="col-span-3 sm:col-span-1">
              <dt class="text-xs text-blue-800 dark:text-blue-300">Created on</dt>
              <dd class="font-semibold text-blue-900 dark:text-blue-100">
                {{ fmtDateLong(wikiDetails.created_at || wikiDetails.uploaded_at) }}
              </dd>
            </div>
          </div>
          <!-- latest state: total bytes, who, when -->
          <div class="rounded-lg border border-green-200 dark:border-green-900
                      bg-green-50 dark:bg-green-950/40 p-3 grid grid-cols-3 gap-2 text-sm">
            <div>
              <dt class="text-xs text-green-800 dark:text-green-300">Total bytes</dt>
              <dd class="tabular-nums font-semibold text-green-900 dark:text-green-100">
                {{ (wikiDetails.bytes ?? wikiDetails.size)?.toLocaleString() ?? '—' }}
              </dd>
            </div>
            <div>
              <dt class="text-xs text-green-800 dark:text-green-300">Last updated by</dt>
              <dd class="font-semibold text-green-900 dark:text-green-100">
                {{ wikiDetails.last_updated_by || '—' }}
              </dd>
            </div>
            <div class="col-span-3 sm:col-span-1">
              <dt class="text-xs text-green-800 dark:text-green-300">Updated on</dt>
              <dd class="font-semibold text-green-900 dark:text-green-100">
                {{ fmtDateLong(wikiDetails.last_updated) }}
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

      <!-- per-submission detail: breakdown, reviews, claims -->
      <p v-if="detailState === 'loading'"
         class="text-sm text-neutral-600 dark:text-neutral-300">
        Loading points breakdown…
      </p>
      <p v-else-if="detailState === 'error'"
         class="text-sm text-red-600 dark:text-red-400">
        Could not load the points breakdown.
      </p>
      <template v-else-if="detail">
        <!-- points breakdown -->
        <div v-if="detail.breakdown.length">
          <h5 class="label">Points breakdown</h5>
          <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div v-for="(line, i) in detail.breakdown" :key="i"
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
        <div v-if="detail.reviews.length">
          <h5 class="label">Reviews</h5>
          <div v-for="r in detail.reviews" :key="r.id" class="text-sm py-1 flex gap-2 items-baseline">
            <b>{{ r.reviewer.username }}</b>
            <span class="badge" :class="claimStatusStyles[r.decision === 'accept' ? 'verified' : r.decision === 'reject' ? 'rejected' : 'claimed']">{{ r.decision }}</span>
            <span class="tabular-nums">{{ r.total }} pts</span>
            <span class="text-neutral-600 dark:text-neutral-300">{{ r.comment }}</span>
          </div>
        </div>

        <!-- claims (self mode) -->
        <div v-if="selfMode && detail.claims.length">
          <h5 class="label">Claims</h5>
          <div v-for="c in detail.claims" :key="c.id" class="text-sm py-1 flex flex-wrap gap-2 items-center">
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

        <!-- claim editor for the owner; keyed so it re-reads fresh claims -->
        <div v-if="selfMode && currentUsername === s.user.username && campaign.status !== 'archived'">
          <h5 class="label">Claim your points</h5>
          <ClaimEditor :key="detailVersion" :rules="campaign.rules" :submission="detail"
                       @save="claims => emit('save-claims', s, claims)" />
        </div>

        <!-- review form for jurors -->
        <div v-if="isJury && campaign.scoring_mode !== 'self' && currentUsername !== s.user.username && campaign.status !== 'archived'">
          <h5 class="label">Your review</h5>
          <ReviewForm :key="detailVersion" :criteria="criteria"
                      :existing="detail.reviews.find(r => r.reviewer.username === currentUsername)"
                      @save="review => emit('save-review', s, review)" />
        </div>
      </template>

      <!-- actions -->
      <div class="flex flex-wrap gap-2 pt-1">
        <button v-if="['article', 'wikidata_item'].includes(s.kind)"
                class="btn" @click.stop="showPreview = true">
          Preview
        </button>
        <button class="btn" :disabled="isPending('refresh')" @click="emit('refresh', s)">
          <svg v-if="isPending('refresh')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Refresh wiki data
        </button>
        <button v-if="currentUsername === s.user.username && campaign.status === 'active'"
                class="btn-danger" :disabled="isPending('withdraw')" @click="emit('withdraw', s)">
          <svg v-if="isPending('withdraw')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Withdraw
        </button>
        <template v-if="isOrganizer">
          <button class="btn-success" :disabled="isPending('accepted')" @click="emit('moderate', s, 'accepted')">
            <svg v-if="isPending('accepted')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Accept
          </button>
          <button class="btn-danger" :disabled="isPending('rejected')" @click="emit('moderate', s, 'rejected')">
            <svg v-if="isPending('rejected')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Reject
          </button>
          <button class="btn-warning" :disabled="isPending('override')" @click="emit('override', s)">
            <svg v-if="isPending('override')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Override points
          </button>
        </template>
        <button v-if="isOrganizer || currentUsername === s.user.username"
                class="btn" :disabled="isPending('recalculate')"
                :title="isOrganizer
                  ? 'Refetch wiki data and rescore from the campaign rules, clearing any override'
                  : 'Refetch wiki data and rescore from the campaign rules (an existing organizer override, if any, is kept)'"
                @click="emit('recalculate', s)">
          <svg v-if="isPending('recalculate')" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Recalculate points
        </button>
      </div>
    </div>

    <SubmissionPreview v-if="showPreview" :submission="s"
                       @close="showPreview = false" />
  </div>
</template>
