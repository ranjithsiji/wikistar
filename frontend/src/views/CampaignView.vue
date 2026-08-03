<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { CdxButton } from '@wikimedia/codex'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'
import AppMessage from '../components/AppMessage.vue'
import ParticipantDetails from '../components/ParticipantDetails.vue'
import StatsTab from '../components/StatsTab.vue'
import CampaignSubmitForm from '../components/campaign/CampaignSubmitForm.vue'
import CampaignOverviewTab from '../components/campaign/CampaignOverviewTab.vue'
import CampaignRulesTab from '../components/campaign/CampaignRulesTab.vue'
import CampaignSuggestedTab from '../components/campaign/CampaignSuggestedTab.vue'
import CampaignSubmissionsTab from '../components/campaign/CampaignSubmissionsTab.vue'
import CampaignLeaderboardTab from '../components/campaign/CampaignLeaderboardTab.vue'

const props = defineProps({
  slug: { type: String, required: true },
  tab: { type: String, default: '' }
})
const router = useRouter()
const auth = useAuthStore()

const campaign = ref(null)
const submissions = ref([])
const leaderboard = ref([])
const stats = ref(null)
const detailsUser = ref(null)   // leaderboard row whose popup is open
const error = ref('')
const notice = ref('')
// The active tab lives in the URL (/campaigns/<slug>/<tab>) so it's
// shareable/bookmarkable and survives a refresh; :tab is empty on the
// bare /campaigns/<slug> path, which means "overview".
const tab = ref(props.tab || 'overview')
const newTitle = ref('')
const newKind = ref('article')
const newLanguage = ref('')
const newUsername = ref('')   // coordinators: who the submission is for

const isOrganizer = computed(() =>
  auth.isAdmin || campaign.value?.my_roles.includes('organizer'))
const isJury = computed(() =>
  isOrganizer.value || campaign.value?.my_roles.includes('jury'))
const isParticipant = computed(() =>
  campaign.value?.my_roles.includes('participant'))
const selfMode = computed(() =>
  ['self', 'hybrid'].includes(campaign.value?.scoring_mode))
const criteria = computed(() => campaign.value?.settings?.jury_criteria || [])

// Optional logo: a Commons file name rendered through Special:FilePath.
const logoUrl = computed(() => {
  const file = (campaign.value?.settings?.logo || '').replace(/^File:/i, '').trim()
  return file
    ? `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(file)}?width=192`
    : ''
})
const logoPageUrl = computed(() => {
  const file = (campaign.value?.settings?.logo || '').replace(/^File:/i, '').trim()
  return file ? `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(file)}` : ''
})

// Bulk kinds are offered only when the campaign carries matching rules.
const hasMetricRule = (applies, metrics) =>
  (campaign.value?.rules || []).some(r =>
    r.rule_type === 'per_unit' && metrics.includes(r.metric)
    && ['any', applies].includes(r.applies_to))
const allowWikidataEdits = computed(() =>
  hasMetricRule('wikidata_item', ['statements', 'labels_descriptions_aliases']))
const allowCommonsEdits = computed(() =>
  hasMetricRule('commons_file', ['image_added', 'depicts_added']))

// Wiki the title autocomplete searches, following project + type.
const submitWiki = computed(() => {
  if (newKind.value === 'wikidata_item') return 'www.wikidata.org'
  if (newKind.value === 'commons_file') return 'commons.wikimedia.org'
  if (campaign.value?.settings?.multi_language) {
    return `${newLanguage.value || campaign.value.language}.wikipedia.org`
  }
  return campaign.value?.wiki_domain
})
const participantNames = computed(() =>
  [...new Set((campaign.value?.members || [])
    .filter(m => m.role === 'participant')
    .map(m => m.user.username))])

// Submissions still needing attention from whoever runs the campaign.
// In jury mode that means "nobody has reviewed it"; in self-assessment
// there are no jury reviews to wait on, so it means "not yet accepted or
// rejected by an organizer" — hence the different tab name.
const reviewBacklog = computed(() => {
  if (!isJury.value) return []
  return submissions.value.filter(s =>
    campaign.value?.scoring_mode === 'jury'
      // A rejected submission is already decided — not a backlog.
      ? s.status !== 'rejected' && !s.reviews.length
      : s.status === 'submitted')
})

const tabs = computed(() => {
  const t = [['overview', 'Overview'], ['submissions', 'Submissions']]
  if (isJury.value) {
    t.push(['review', campaign.value?.scoring_mode === 'jury'
      ? 'Not reviewed' : 'Review'])
  }
  if (campaign.value?.suggested_articles.length || campaign.value?.suggested_items.length) {
    t.push(['suggested', 'Suggested articles'])
  }
  t.push(['leaderboard', 'Leaderboard'], ['rules', 'Scoring rules'], ['stats', 'Statistics'])
  return t
})

const canApprove = ref(false)

async function load () {
  try {
    const [campaignRes, submissionsRes] = await Promise.all([
      api.getCampaign(props.slug), api.listSubmissions(props.slug)
    ])
    campaign.value = campaignRes.data
    submissions.value = submissionsRes.data
    // Overview stat tiles; best-effort, never blocks the page. One
    // retry: a transient timeout otherwise leaves the tiles empty until
    // the user reloads the whole page.
    const loadStats = (retriesLeft) => {
      api.campaignStats(props.slug)
        .then(r => { stats.value = r.data })
        .catch(() => {
          if (retriesLeft > 0) setTimeout(() => loadStats(retriesLeft - 1), 4000)
        })
    }
    loadStats(1)
    // Leaderboard preview on Overview; silent if private (403) or empty.
    api.leaderboard(props.slug)
      .then(r => { leaderboard.value = r.data })
      .catch(() => {})
    if (!newLanguage.value) newLanguage.value = campaign.value.language
    // Fountain model: approval needs on-wiki admin rights (jury: sysop on
    // the target wiki; self: sysop on any Wikipedia), or site admin.
    if (campaign.value.status === 'draft' && auth.isLoggedIn) {
      canApprove.value = (await api.approvalRights(props.slug)).data.can_approve
    } else {
      canApprove.value = false
    }
    // Suggested items' sitelinks load lazily per active heading — handled
    // entirely inside CampaignSuggestedTab.vue.
  } catch (e) {
    error.value = errorMessage(e)
  }
}
async function loadLeaderboard () {
  try {
    leaderboard.value = (await api.leaderboard(props.slug)).data
  } catch (e) {
    error.value = errorMessage(e)
  }
}
// Submission-only actions (accept/reject/refresh/recalculate/withdraw/
// review/claims) only need submissions refreshed, not the whole
// campaign — reloading campaign+approval-rights on every click made
// "Accept" feel slow for no reason.
async function reloadSubmissions () {
  submissions.value = (await api.listSubmissions(props.slug)).data
}
onMounted(load)

function selectTab (key) {
  tab.value = key
  if (key === 'leaderboard') loadLeaderboard()
  router.push(`/campaigns/${props.slug}/${key}`)
}

// Browser back/forward between tabs, or a direct link to a specific tab.
watch(() => props.tab, (key) => {
  const next = key || 'overview'
  if (next !== tab.value) {
    tab.value = next
    if (next === 'leaderboard') loadLeaderboard()
  }
})

// The review tab exists only for organizers/jury, but its URL is
// reachable by anyone. Drop a participant who lands there (or who loses
// the role) back to the overview instead of an empty panel.
watch([tab, isJury], ([key, jury]) => {
  if (key === 'review' && campaign.value && !jury) {
    tab.value = 'overview'
    router.replace(`/campaigns/${props.slug}`)
  }
})

// Tracks which per-submission (or per-campaign) action button is
// mid-flight, e.g. "42:refresh", so only that button shows a spinner and
// disables itself.
const pendingAction = ref('')
const isCampaignPending = (action) => pendingAction.value === `campaign:${action}`

async function run (fn, successMsg = '', pendingKey = '') {
  error.value = ''
  notice.value = ''
  if (pendingKey) pendingAction.value = pendingKey
  try {
    await fn()
    notice.value = successMsg
    await load()
    if (tab.value === 'leaderboard') await loadLeaderboard()
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    if (pendingKey) pendingAction.value = ''
  }
}
// Same as run(), but for actions that only change one submission —
// refreshes just the submissions list (and the leaderboard, since points
// may have changed) instead of the whole campaign.
async function runSub (fn, successMsg = '', pendingKey = '') {
  error.value = ''
  notice.value = ''
  if (pendingKey) pendingAction.value = pendingKey
  try {
    await fn()
    notice.value = successMsg
    await reloadSubmissions()
    if (tab.value === 'leaderboard') await loadLeaderboard()
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    if (pendingKey) pendingAction.value = ''
  }
}

const join = () => run(() => api.joinCampaign(props.slug), 'You joined the campaign.', 'campaign:join')
const approve = () => run(() => api.approveCampaign(props.slug), 'Campaign approved.', 'campaign:approve')
const deactivate = () => {
  if (!confirm('Deactivate this campaign? It goes back to draft, stops accepting submissions and is hidden from the public until approved again.')) return
  return run(() => api.deactivateCampaign(props.slug), 'Campaign deactivated.', 'campaign:deactivate')
}
const reject = () => {
  const reason = prompt('Reason for rejection?') || ''
  return run(() => api.rejectCampaign(props.slug, reason), '', 'campaign:reject')
}
const remove = async () => {
  if (!confirm('Delete this campaign and all its submissions?')) return
  pendingAction.value = 'campaign:delete'
  try {
    await api.deleteCampaign(props.slug)
    router.push('/')
  } catch (e) {
    error.value = errorMessage(e)
    pendingAction.value = ''
  }
}
const isBulkKind = computed(() =>
  ['wikidata_edits', 'commons_edits'].includes(newKind.value))
const submit = () => run(async () => {
  const payload = { title: isBulkKind.value ? '' : newTitle.value, kind: newKind.value }
  if (campaign.value.settings.multi_language && newKind.value === 'article') {
    payload.language = newLanguage.value || campaign.value.language
  }
  if (isOrganizer.value) payload.username = newUsername.value.trim()
  await api.createSubmission(props.slug, payload)
  newTitle.value = ''
}, 'Submission added.')
const withdraw = (s) => {
  if (!confirm(`Withdraw "${s.title}"?`)) return
  return runSub(() => api.deleteSubmission(s.id), '', `${s.id}:withdraw`)
}
const refresh = (s) => runSub(() => api.refreshSubmission(s.id), 'Wiki metadata refreshed.', `${s.id}:refresh`)
const recalculate = (s) => {
  // Only an organizer's recalculate clears a manual override; the
  // submission owner's recalculate refreshes points but leaves an
  // existing override in place, so no destructive-sounding confirm here.
  if (isOrganizer.value && s.points_override != null && !confirm(
    'This clears the manual points override and recomputes the points '
    + 'from fresh wiki data and the campaign rules. Continue?')) return
  return runSub(() => api.recalculateSubmission(s.id), 'Points recalculated.', `${s.id}:recalculate`)
}
const saveReview = (s, review) => runSub(() => api.submitReview(s.id, review), 'Review saved.')
const saveClaims = (s, claims) => runSub(() => api.saveClaims(s.id, claims), 'Claims saved.')
const moderateSub = (s, status) => {
  let moderation_note
  if (status === 'rejected') {
    moderation_note = prompt('Reason for rejecting this submission (shown to the participant):')
    if (moderation_note === null) return
    moderation_note = moderation_note.trim()
  }
  return runSub(() => api.moderateSubmission(s.id, { status, moderation_note }), '', `${s.id}:${status}`)
}
const overrideSub = (s) => {
  const v = prompt('Final points for this submission (empty to clear the override):')
  if (v === null) return
  const payload = v === '' ? { clear_override: true } : { points_override: Number(v) }
  return runSub(() => api.moderateSubmission(s.id, payload), '', `${s.id}:override`)
}
const moderateClaim = (claim, status) => {
  let points_final = null
  if (status === 'adjusted') {
    const v = prompt('Final points for this claim:')
    if (v === null) return
    points_final = Number(v)
  }
  return runSub(() => api.moderateClaim(claim.id, { status, points_final }))
}

const statusStyles = {
  draft: 'bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300',
  active: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  finished: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  archived: 'bg-neutral-200 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
}
</script>

<template>
  <AppMessage v-if="!campaign && error" v-model="error" type="error" />
  <div v-else-if="!campaign" class="flex flex-col items-center justify-center gap-3 py-24 text-neutral-600 dark:text-neutral-300">
    <svg class="w-8 h-8 animate-spin text-blue-700 dark:text-blue-400" viewBox="0 0 24 24" fill="none">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <p class="text-sm">Loading campaign…</p>
  </div>
  <div v-else>
    <!-- header -->
    <div class="flex flex-wrap items-start gap-3 mb-1">
      <a v-if="logoUrl" :href="logoPageUrl" target="_blank" class="shrink-0" title="Campaign logo (Wikimedia Commons)">
        <img :src="logoUrl" alt="" class="h-14 w-14 object-contain rounded" />
      </a>
      <h1 class="text-2xl font-bold">
        <a v-if="campaign.settings.campaign_page_url"
           :href="campaign.settings.campaign_page_url" target="_blank" rel="noopener"
           class="text-link-700 dark:text-link-400 hover:underline"
           title="Open the campaign page">{{ campaign.name }}</a>
        <template v-else>{{ campaign.name }}</template>
      </h1>
      <span class="badge mt-1.5" :class="statusStyles[campaign.status]">{{ campaign.status }}</span>
      <span class="badge mt-1.5 bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
        {{ { jury: 'Jury scoring', self: 'Self-assessment', hybrid: 'Hybrid' }[campaign.scoring_mode] }}
      </span>
      <div class="flex-1"></div>
      <div class="flex gap-2 flex-wrap">
        <cdx-button v-if="auth.isLoggedIn && campaign.status === 'active' && !isParticipant"
                    action="progressive" weight="primary" :disabled="isCampaignPending('join')" @click="join">
          {{ isCampaignPending('join') ? 'Joining…' : 'Join campaign' }}
        </cdx-button>
        <router-link v-if="isJury && campaign.scoring_mode !== 'self'
                            && ['active', 'finished'].includes(campaign.status)"
                     class="btn-primary" :to="`/campaigns/${slug}/judge`">
          ⚖ Judge
        </router-link>
        <router-link v-if="isOrganizer" class="btn" :to="`/campaigns/${slug}/edit`">Edit</router-link>
        <cdx-button v-if="canApprove && campaign.status === 'draft'"
                    action="progressive" weight="primary" :disabled="isCampaignPending('approve')" @click="approve">
          {{ isCampaignPending('approve') ? 'Approving…' : 'Approve' }}
        </cdx-button>
        <cdx-button v-if="canApprove && campaign.status === 'draft'"
                    action="destructive" weight="primary" :disabled="isCampaignPending('reject')" @click="reject">
          {{ isCampaignPending('reject') ? 'Rejecting…' : 'Reject' }}
        </cdx-button>
        <cdx-button v-if="isOrganizer && campaign.status === 'active'"
                    action="destructive" weight="primary" :disabled="isCampaignPending('deactivate')" @click="deactivate">
          {{ isCampaignPending('deactivate') ? 'Deactivating…' : 'Deactivate' }}
        </cdx-button>
        <cdx-button v-if="isOrganizer && (campaign.status === 'draft' || auth.isAdmin)"
                    action="destructive" weight="primary" :disabled="isCampaignPending('delete')" @click="remove">
          {{ isCampaignPending('delete') ? 'Deleting…' : 'Delete' }}
        </cdx-button>
      </div>
    </div>
    <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
      <span class="font-semibold text-neutral-900 dark:text-neutral-100">
        {{ campaign.start_date }} → {{ campaign.end_date }}
      </span>
      <template v-if="!campaign.settings.multi_language"> · {{ campaign.wiki_domain }}</template>
      · {{ campaign.submission_count }} submissions · {{ campaign.participant_count }} participants
    </p>

    <AppMessage v-model="error" type="error" />
    <AppMessage v-model="notice" type="success" />

    <div class="tab-group w-fit max-w-full overflow-x-auto">
      <button v-for="[key, label] in tabs" :key="key" class="tab"
              :class="{ 'tab-active': tab === key }"
              @click="selectTab(key)">
        {{ label }}
      </button>
    </div>

    <div class="tab-panel p-4">
    <!-- submit form: on the campaign home page and the submissions tab.
         The Overview tab gets a highlighted "Contribute" CTA card; the
         Submissions tab keeps the plain working-list styling. -->
    <CampaignSubmitForm v-if="tab === 'overview' || tab === 'submissions'"
                        :tab="tab" :campaign="campaign" :is-logged-in="auth.isLoggedIn"
                        :is-organizer="isOrganizer" :participant-names="participantNames"
                        :allow-wikidata-edits="allowWikidataEdits" :allow-commons-edits="allowCommonsEdits"
                        :submit-wiki="submitWiki"
                        v-model:new-username="newUsername" v-model:new-language="newLanguage"
                        v-model:new-kind="newKind" v-model:new-title="newTitle"
                        @submit="submit" />

    <!-- OVERVIEW -->
    <CampaignOverviewTab v-if="tab === 'overview'"
                        :campaign="campaign" :stats="stats" :leaderboard="leaderboard"
                        @view-leaderboard="selectTab('leaderboard')"
                        @show-details="detailsUser = $event" />

    <!-- SCORING RULES -->
    <CampaignRulesTab v-if="tab === 'rules'" :campaign="campaign" />

    <!-- SUGGESTED ARTICLES -->
    <CampaignSuggestedTab v-if="tab === 'suggested'" :slug="slug" :campaign="campaign"
                        @error="error = $event" />

    <!-- SUBMISSIONS -->
    <CampaignSubmissionsTab v-if="tab === 'submissions'"
                        :campaign="campaign" :submissions="submissions"
                        :is-logged-in="auth.isLoggedIn" :current-username="auth.user?.username || ''"
                        :is-organizer="isOrganizer" :is-jury="isJury"
                        :self-mode="selfMode" :criteria="criteria"
                        :pending-action="pendingAction"
                        @refresh="refresh" @withdraw="withdraw" @moderate="moderateSub"
                        @override="overrideSub" @recalculate="recalculate"
                        @save-review="saveReview" @save-claims="saveClaims"
                        @moderate-claim="moderateClaim" />

    <!-- REVIEW BACKLOG: the same submissions list, pre-filtered to what
         still needs attention, so it keeps every moderation control. -->
    <template v-if="tab === 'review'">
      <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-3">
        <template v-if="reviewBacklog.length">
          {{ reviewBacklog.length }}
          {{ campaign.scoring_mode === 'jury'
            ? 'submission(s) no juror has reviewed yet.'
            : 'submission(s) waiting to be accepted or rejected.' }}
        </template>
        <template v-else>
          Nothing is waiting — every submission has been
          {{ campaign.scoring_mode === 'jury' ? 'reviewed' : 'moderated' }}.
        </template>
      </p>
      <CampaignSubmissionsTab v-if="reviewBacklog.length"
                          :campaign="campaign" :submissions="reviewBacklog"
                          :is-logged-in="auth.isLoggedIn" :current-username="auth.user?.username || ''"
                          :is-organizer="isOrganizer" :is-jury="isJury"
                          :self-mode="selfMode" :criteria="criteria"
                          :pending-action="pendingAction"
                          @refresh="refresh" @withdraw="withdraw" @moderate="moderateSub"
                          @override="overrideSub" @recalculate="recalculate"
                          @save-review="saveReview" @save-claims="saveClaims"
                          @moderate-claim="moderateClaim" />
    </template>

    <!-- LEADERBOARD -->
    <CampaignLeaderboardTab v-if="tab === 'leaderboard'"
                        :leaderboard="leaderboard" :current-username="auth.user?.username || ''"
                        :show-podium="campaign.settings.show_leaderboard_podium"
                        @show-details="detailsUser = $event" />

    <!-- STATISTICS -->
    <StatsTab v-if="tab === 'stats'" :slug="slug" />
    </div>

    <ParticipantDetails v-if="detailsUser" :slug="slug" :user="detailsUser"
                        @close="detailsUser = null" />
  </div>
</template>
