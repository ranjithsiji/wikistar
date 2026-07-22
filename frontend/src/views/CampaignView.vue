<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { CdxButton, CdxTable } from '@wikimedia/codex'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'
import AppMessage from '../components/AppMessage.vue'
import ClaimEditor from '../components/ClaimEditor.vue'
import LanguageSelect from '../components/LanguageSelect.vue'
import ParticipantDetails from '../components/ParticipantDetails.vue'
import ReviewForm from '../components/ReviewForm.vue'
import StatsTab from '../components/StatsTab.vue'
import TitleAutocomplete from '../components/TitleAutocomplete.vue'
import UserSelect from '../components/UserSelect.vue'

const props = defineProps({ slug: { type: String, required: true } })
const router = useRouter()
const auth = useAuthStore()

const campaign = ref(null)
const submissions = ref([])
const leaderboard = ref([])
const lbColumns = [
  { id: 'rank', label: '#', textAlign: 'number' },
  { id: 'username', label: 'Participant', allowSort: true },
  { id: 'submission_count', label: 'Submissions', textAlign: 'number', allowSort: true },
  { id: 'points', label: 'Points', textAlign: 'number', allowSort: true }
]
const lbSort = ref({})
const lbRows = computed(() => {
  const rows = leaderboard.value.map(r => ({
    rank: r.rank, username: r.user.username,
    submission_count: r.submission_count, points: r.points, user: r.user
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
const leaderboardPreview = computed(() => leaderboard.value.slice(0, 5))
const lbPreviewColumns = [
  { id: 'rank', label: '#', textAlign: 'number' },
  { id: 'username', label: 'Participant' },
  { id: 'submission_count', label: 'Submissions', textAlign: 'number' },
  { id: 'points', label: 'Points', textAlign: 'number' }
]
const lbPreviewRows = computed(() => leaderboardPreview.value.map(r => ({
  rank: r.rank, username: r.user.username,
  submission_count: r.submission_count, points: r.points, user: r.user
})))
const stats = ref(null)
const detailsUser = ref(null)   // leaderboard row whose popup is open
const error = ref('')
const notice = ref('')
const tab = ref('overview')
const onlyMine = ref(false)
const expanded = ref(null)
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
// Coordinators can narrow the submission list to one participant.
const filterUser = ref('')
const submitterNames = computed(() =>
  [...new Set(submissions.value.map(s => s.user.username))]
    .sort((a, b) => a.localeCompare(b)))

const shownSubmissions = computed(() => {
  let list = submissions.value
  if (onlyMine.value) list = list.filter(s => s.user.username === auth.user?.username)
  if (filterUser.value) list = list.filter(s => s.user.username === filterUser.value)
  return list
})

// Jury mode gets a Fountain-style table grouped by participant; self /
// hybrid keep the flat expandable list (one pseudo-group without header).
const juryTable = computed(() => campaign.value?.scoring_mode === 'jury')
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
const isBulkKind = computed(() =>
  ['wikidata_edits', 'commons_edits'].includes(newKind.value))

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

const overviewTiles = computed(() => [
  { label: 'Submissions', value: stats.value?.submissions },
  { label: 'Participants', value: stats.value?.participants },
  { label: 'Total points', value: stats.value?.total_points },
  { label: 'Reviews', value: stats.value?.reviews }
])

const tabs = computed(() => {
  const t = [['overview', 'Overview'], ['submissions', 'Submissions']]
  if (campaign.value?.suggested_articles.length || campaign.value?.suggested_items.length) {
    t.push(['suggested', 'Suggested articles'])
  }
  t.push(['leaderboard', 'Leaderboard'], ['stats', 'Statistics'])
  return t
})

const canApprove = ref(false)

// Tab structure (heading -> QIDs) comes straight from the campaign
// payload — already loaded, no Wikidata round-trip needed just to know
// what headings exist. Sitelinks (labels/links, the slow part) are
// fetched lazily, one heading at a time, only for the section being
// viewed — a big suggested list no longer means resolving every item on
// every visit or on every "add language" click.
const suggestedSections = computed(() => {
  const order = []
  const byHeading = new Map()
  for (const item of campaign.value?.suggested_items || []) {
    const h = item.section || ''
    if (!byHeading.has(h)) { byHeading.set(h, []); order.push(h) }
    byHeading.get(h).push(item.qid)
  }
  return order.map(h => ({ heading: h, qids: byHeading.get(h) }))
})
const activeSection = ref('')
watch(suggestedSections, (secs) => {
  if (secs.length && !secs.some(s => s.heading === activeSection.value)) {
    activeSection.value = secs[0].heading
  }
})

// Resolved sitelinks per heading: { languages, items } | 'loading' | 'error'.
const sectionCache = ref({})
const activeSectionData = computed(() => {
  const v = sectionCache.value[activeSection.value]
  return (v && v !== 'loading' && v !== 'error') ? v : null
})
const activeSectionLoading = computed(() =>
  sectionCache.value[activeSection.value] === 'loading')
const activeSectionFailed = computed(() =>
  sectionCache.value[activeSection.value] === 'error')

async function loadSection (heading, extraLangs = []) {
  const sec = suggestedSections.value.find(s => s.heading === heading)
  if (!sec) return
  const prior = sectionCache.value[heading]
  const priorLangs = (prior && prior !== 'loading' && prior !== 'error')
    ? prior.languages : []
  const langs = [...new Set([...priorLangs, ...extraLangs])]
  sectionCache.value = { ...sectionCache.value, [heading]: 'loading' }
  try {
    const { data } = await api.suggestedLinks(props.slug,
      langs.length ? langs : null, sec.qids)
    sectionCache.value = { ...sectionCache.value, [heading]: data }
  } catch (e) {
    sectionCache.value = { ...sectionCache.value, [heading]: 'error' }
    error.value = errorMessage(e)
  }
}
// Fetch whichever heading becomes active, the first time it's viewed.
watch(activeSection, (h) => {
  if (h && !sectionCache.value[h]) loadSection(h)
}, { immediate: true })

// Suggested-items table: English first, then the preference languages
// (the backend always includes "en" in the response).
const suggestedLangs = computed(() => {
  const langs = activeSectionData.value?.languages || []
  return ['en', ...langs.filter(l => l !== 'en')]
})
const itemLink = (item, lang) => item.links.find(l => l.lang === lang)
const shownSectionItems = computed(() => activeSectionData.value?.items || [])

// Two heading layouts, user-switchable (remembered per device):
//   all      — every heading as a wrapped label button (default)
//   compact  — hamburger menu on the left + at most three tabs
const sectionViewMode = ref(localStorage.getItem('suggestedSectionsView') || 'all')
function toggleSectionView () {
  sectionViewMode.value = sectionViewMode.value === 'all' ? 'compact' : 'all'
  localStorage.setItem('suggestedSectionsView', sectionViewMode.value)
}
const MAX_SECTION_TABS = 3
const sectionMenuOpen = ref(false)
const sectionMenuRoot = ref(null)
const visibleSections = computed(() => {
  const secs = suggestedSections.value
  if (secs.length <= MAX_SECTION_TABS) return secs
  const vis = secs.slice(0, MAX_SECTION_TABS)
  if (!vis.some(s => s.heading === activeSection.value)) {
    const active = secs.find(s => s.heading === activeSection.value)
    if (active) vis[MAX_SECTION_TABS - 1] = active
  }
  return vis
})
function onSectionMenuDocClick (e) {
  if (sectionMenuRoot.value && !sectionMenuRoot.value.contains(e.target)) {
    sectionMenuOpen.value = false
  }
}
onMounted(() => document.addEventListener('click', onSectionMenuDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onSectionMenuDocClick))

// Add an extra language column to the suggested-items table on the fly —
// re-resolves only the active heading's items, not the whole suggested
// list, so this stays fast even with many headings/items.
const addingLang = ref('')
async function addSuggestedLang () {
  const code = addingLang.value
  if (!code || !activeSection.value) return
  addingLang.value = ''
  await loadSection(activeSection.value, [code])
}
// Red-link style "start this article" URL, prefilled with the English title.
function createUrl (item, lang) {
  const title = (item.label_en || item.qid).replaceAll(' ', '_')
  return `https://${lang}.wikipedia.org/w/index.php?title=${encodeURIComponent(title)}&action=edit&redlink=1`
}

async function load () {
  try {
    campaign.value = (await api.getCampaign(props.slug)).data
    submissions.value = (await api.listSubmissions(props.slug)).data
    // Overview stat tiles; best-effort, never blocks the page.
    api.campaignStats(props.slug)
      .then(r => { stats.value = r.data })
      .catch(() => {})
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
    // Suggested items' sitelinks load lazily per active heading — see the
    // `activeSection` watcher — once `suggestedSections` picks one up.
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
onMounted(load)

async function run (fn, successMsg = '') {
  error.value = ''
  notice.value = ''
  try {
    await fn()
    notice.value = successMsg
    await load()
    if (tab.value === 'leaderboard') await loadLeaderboard()
  } catch (e) {
    error.value = errorMessage(e)
  }
}

const join = () => run(() => api.joinCampaign(props.slug), 'You joined the campaign.')
const approve = () => run(() => api.approveCampaign(props.slug), 'Campaign approved.')
const deactivate = () => {
  if (!confirm('Deactivate this campaign? It goes back to draft, stops accepting submissions and is hidden from the public until approved again.')) return
  return run(() => api.deactivateCampaign(props.slug), 'Campaign deactivated.')
}
const reject = () => {
  const reason = prompt('Reason for rejection?') || ''
  return run(() => api.rejectCampaign(props.slug, reason))
}
const remove = async () => {
  if (!confirm('Delete this campaign and all its submissions?')) return
  try {
    await api.deleteCampaign(props.slug)
    router.push('/')
  } catch (e) { error.value = errorMessage(e) }
}
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
  return run(() => api.deleteSubmission(s.id))
}
const refresh = (s) => run(() => api.refreshSubmission(s.id), 'Wiki metadata refreshed.')
const recalculate = (s) => {
  if (s.points_override != null && !confirm(
    'This clears the manual points override and recomputes the points '
    + 'from fresh wiki data and the campaign rules. Continue?')) return
  return run(() => api.recalculateSubmission(s.id), 'Points recalculated.')
}
const saveReview = (s, review) => run(() => api.submitReview(s.id, review), 'Review saved.')
const saveClaims = (s, claims) => run(() => api.saveClaims(s.id, claims), 'Claims saved.')
const moderateSub = (s, status) => run(() => api.moderateSubmission(s.id, { status }))
const overrideSub = (s) => {
  const v = prompt('Final points for this submission (empty to clear the override):')
  if (v === null) return
  const payload = v === '' ? { clear_override: true } : { points_override: Number(v) }
  return run(() => api.moderateSubmission(s.id, payload))
}
const moderateClaim = (claim, status) => {
  let points_final = null
  if (status === 'adjusted') {
    const v = prompt('Final points for this claim:')
    if (v === null) return
    points_final = Number(v)
  }
  return run(() => api.moderateClaim(claim.id, { status, points_final }))
}

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
  return campaign.value?.rules.find(r => r.id === id)?.label || `rule ${id}`
}
</script>

<template>
  <AppMessage v-if="!campaign && error" v-model="error" type="error" />
  <p v-else-if="!campaign" class="text-neutral-600 dark:text-neutral-300">Loading…</p>
  <div v-else>
    <!-- header -->
    <div class="flex flex-wrap items-start gap-3 mb-1">
      <a v-if="logoUrl" :href="logoPageUrl" target="_blank" class="shrink-0" title="Campaign logo (Wikimedia Commons)">
        <img :src="logoUrl" alt="" class="h-14 w-14 object-contain rounded" />
      </a>
      <h1 class="text-2xl font-bold">{{ campaign.name }}</h1>
      <span class="badge mt-1.5" :class="statusStyles[campaign.status]">{{ campaign.status }}</span>
      <span class="badge mt-1.5 bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
        {{ { jury: 'Jury scoring', self: 'Self-assessment', hybrid: 'Hybrid' }[campaign.scoring_mode] }}
      </span>
      <div class="flex-1"></div>
      <div class="flex gap-2 flex-wrap">
        <cdx-button v-if="auth.isLoggedIn && campaign.status === 'active' && !isParticipant"
                    action="progressive" weight="primary" @click="join">Join campaign</cdx-button>
        <router-link v-if="isJury && campaign.scoring_mode !== 'self'
                            && ['active', 'finished'].includes(campaign.status)"
                     class="btn-primary" :to="`/campaigns/${slug}/judge`">
          ⚖ Judge
        </router-link>
        <router-link v-if="isOrganizer" class="btn" :to="`/campaigns/${slug}/edit`">Edit</router-link>
        <cdx-button v-if="canApprove && campaign.status === 'draft'"
                    action="progressive" weight="primary" @click="approve">Approve</cdx-button>
        <cdx-button v-if="canApprove && campaign.status === 'draft'"
                    action="destructive" weight="primary" @click="reject">Reject</cdx-button>
        <cdx-button v-if="isOrganizer && campaign.status === 'active'"
                    action="destructive" weight="primary" @click="deactivate">Deactivate</cdx-button>
        <cdx-button v-if="isOrganizer && (campaign.status === 'draft' || auth.isAdmin)"
                    action="destructive" weight="primary" @click="remove">Delete</cdx-button>
      </div>
    </div>
    <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
      {{ campaign.start_date }} → {{ campaign.end_date }} · {{ campaign.wiki_domain }}
      · {{ campaign.submission_count }} submissions · {{ campaign.participant_count }} participants
      <template v-if="campaign.settings.campaign_page_url">
        · <a :href="campaign.settings.campaign_page_url" target="_blank"
             class="text-blue-600 dark:text-blue-400 hover:underline">Campaign page ↗</a>
      </template>
    </p>

    <AppMessage v-model="error" type="error" />
    <AppMessage v-model="notice" type="success" />

    <div class="tab-group mb-4 w-fit max-w-full overflow-x-auto">
      <button v-for="[key, label] in tabs" :key="key" class="tab"
              :class="{ 'tab-active': tab === key }"
              @click="tab = key; if (key === 'leaderboard') loadLeaderboard()">
        {{ label }}
      </button>
    </div>

    <!-- submit form: on the campaign home page and the submissions tab -->
    <template v-if="tab === 'overview' || tab === 'submissions'">
      <div v-if="auth.isLoggedIn && campaign.status === 'active'" class="card p-4 mb-4">
        <form class="flex flex-wrap gap-2 items-end" @submit.prevent="submit">
          <!-- coordinators submit on behalf of a participant -->
          <div v-if="isOrganizer" class="w-56">
            <label class="label">Username</label>
            <UserSelect v-model="newUsername" required :participants="participantNames"
                        title="Coordinators submit on behalf of this participant" />
          </div>
          <!-- project first: it decides where the title is looked up -->
          <div v-if="campaign.settings.multi_language && newKind === 'article'" class="w-56">
            <label class="label">Project (language)</label>
            <LanguageSelect v-model="newLanguage" />
          </div>
          <div v-if="campaign.settings.allow_wikidata_items || campaign.settings.allow_commons_files
                     || allowWikidataEdits || allowCommonsEdits">
            <label class="label">Type</label>
            <select v-model="newKind" class="input">
              <option value="article">Article</option>
              <option v-if="campaign.settings.allow_wikidata_items" value="wikidata_item">Wikidata item</option>
              <option v-if="campaign.settings.allow_commons_files" value="commons_file">Commons file</option>
              <option v-if="allowWikidataEdits" value="wikidata_edits">Wikidata edits (whole period)</option>
              <option v-if="allowCommonsEdits" value="commons_edits">Commons uploads (whole period)</option>
            </select>
          </div>
          <div v-if="!isBulkKind" class="flex-1 min-w-48">
            <label class="label">{{ { article: 'Article title', wikidata_item: 'Item QID', commons_file: 'File name' }[newKind] }}</label>
            <TitleAutocomplete v-model="newTitle" required
                               :wiki="submitWiki" :kind="newKind"
                               :placeholder="{ article: 'Start typing or paste the article title…', wikidata_item: 'Q… or search by label', commons_file: 'File:Example.jpg' }[newKind]" />
          </div>
          <p v-else class="flex-1 min-w-48 text-xs text-neutral-600 dark:text-neutral-300 self-center">
            {{ newKind === 'wikidata_edits'
               ? 'Counts the statements and label/description/alias edits made on eligible items during the campaign.'
               : 'Counts the files uploaded and depicts statements added during the campaign.' }}
          </p>
          <button class="btn-primary" type="submit">Submit contribution</button>
        </form>
      </div>
      <p v-else-if="!auth.isLoggedIn && campaign.status === 'active'"
         class="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
        <a class="text-blue-600 dark:text-blue-400 hover:underline" :href="api.loginUrl">Log in</a>
        to submit your contribution.
      </p>
    </template>

    <!-- OVERVIEW -->
    <div v-if="tab === 'overview'" class="space-y-4">
      <!-- headline statistics -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div v-for="t in overviewTiles" :key="t.label" class="card p-4">
          <div class="text-2xl font-bold tabular-nums">{{ t.value ?? '—' }}</div>
          <div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">{{ t.label }}</div>
        </div>
      </div>

      <div class="card p-4" v-if="campaign.description">
        <p class="text-sm whitespace-pre-wrap">{{ campaign.description }}</p>
      </div>

      <!-- people: one row, groups side by side -->
      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-2">People</h4>
        <div class="flex flex-wrap gap-x-10 gap-y-2 text-sm">
          <div class="flex flex-wrap items-baseline gap-1.5">
            <b>Organizers:</b>
            <template v-if="campaign.members.some(m => m.role === 'organizer')">
              <span v-for="m in campaign.members.filter(m => m.role === 'organizer')" :key="m.id"
                    class="badge bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                {{ m.user.username }}
              </span>
            </template>
            <span v-else>—</span>
          </div>
          <div class="flex flex-wrap items-baseline gap-1.5">
            <b>Jury:</b>
            <template v-if="campaign.members.some(m => m.role === 'jury')">
              <span v-for="m in campaign.members.filter(m => m.role === 'jury')" :key="m.id"
                    class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
                {{ m.user.username }}
              </span>
            </template>
            <span v-else>—</span>
          </div>
        </div>
      </div>

      <!-- leaderboard preview: top 5, link through to the full tab -->
      <div class="card p-4" v-if="leaderboardPreview.length">
        <div class="flex items-center justify-between mb-2">
          <h4 class="font-semibold text-sm">Leaderboard</h4>
          <cdx-button action="progressive" weight="quiet" size="small"
                      @click="tab = 'leaderboard'; loadLeaderboard()">
            View full leaderboard →
          </cdx-button>
        </div>
        <cdx-table caption="Top participants" :hide-caption="true"
                   :columns="lbPreviewColumns" :data="lbPreviewRows">
          <template #item-username="{ item, row }">
            <button type="button" title="Show this participant's submissions"
                    class="font-medium text-blue-700 dark:text-blue-400 hover:underline"
                    @click="detailsUser = row.user">{{ item }}</button>
          </template>
          <template #item-points="{ item }">
            <span class="tabular-nums font-semibold">{{ item }}</span>
          </template>
        </cdx-table>
      </div>

      <div class="grid md:grid-cols-2 gap-4">
        <div class="card p-4 md:col-span-2">
          <h4 class="font-semibold text-sm mb-2">Scoring rules</h4>
          <p v-if="!campaign.rules.length" class="text-sm text-neutral-600 dark:text-neutral-300">
            Points are given by the jury.
          </p>
          <table v-else class="w-full">
            <tbody>
              <tr v-for="r in campaign.rules" :key="r.id"
                  class="border-t border-neutral-100 dark:border-neutral-800 first:border-0">
                <td class="td pl-0">{{ r.label }}</td>
                <td class="td text-xs text-neutral-600 dark:text-neutral-300">{{ r.applies_to.replace('_', ' ') }}</td>
                <td class="td pr-0 text-right tabular-nums">
                  <template v-if="r.rule_type === 'per_unit'">{{ r.points }} / {{ r.unit_size }}</template>
                  <template v-else-if="['flat_bonus', 'suggested_list'].includes(r.rule_type)">+{{ r.points }}</template>
                  <template v-else>—</template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SUGGESTED ARTICLES -->
    <div v-if="tab === 'suggested'" class="space-y-4">
      <div class="card p-4" v-if="campaign.suggested_articles.length">
        <h4 class="font-semibold text-sm mb-2">Suggested articles (bonus points)</h4>
        <ul class="space-y-1 text-sm list-disc pl-5 sm:columns-2 lg:columns-3">
          <li v-for="t in campaign.suggested_articles" :key="t">
            <a target="_blank"
               :href="`https://${campaign.wiki_domain}/wiki/${t.replaceAll(' ', '_')}`"
               class="text-blue-700 dark:text-blue-400 hover:underline">{{ t }}</a>
          </li>
        </ul>
      </div>
      <div class="card" v-if="campaign.suggested_items.length">
        <div class="px-4 pt-4">
          <h4 class="font-semibold text-sm">Suggested Wikidata items (bonus points)</h4>
        </div>

        <!-- separate, highlighted block: add a language to check article coverage -->
        <div class="mx-4 mt-3 rounded-lg border border-blue-200 dark:border-blue-900
                    bg-blue-50 dark:bg-blue-950/40 p-3">
          <p class="text-xs text-blue-900 dark:text-blue-200 mb-2">
            Add a language to check whether an article on each suggested item
            in the current tab already exists in that language, and get a
            direct link to create it if not.
          </p>
          <form class="flex flex-wrap items-center gap-2" @submit.prevent="addSuggestedLang">
            <LanguageSelect v-model="addingLang" class="!w-56" placeholder="Add a language…" />
            <button class="btn-primary"
                    :disabled="!addingLang || activeSectionLoading
                      || (activeSectionData?.languages.length || 0) >= 10">
              Add language
            </button>
            <span v-if="activeSectionLoading"
                  class="inline-flex items-center gap-1.5 text-xs text-blue-800 dark:text-blue-300">
              <svg class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Checking Wikidata for this tab…
            </span>
          </form>
        </div>
        <div class="mt-2">
          <!-- heading picker: all headings as buttons (default), or a
               compact bar with a hamburger menu on the left -->
          <template v-if="suggestedSections.length > 1 || suggestedSections[0]?.heading">
            <!-- all headings, wrapped -->
            <div v-if="sectionViewMode === 'all'"
                 class="flex flex-wrap items-center gap-2 px-4 py-3
                        border-b border-neutral-200 dark:border-neutral-800">
              <button v-for="sec in suggestedSections" :key="sec.heading" type="button"
                      class="rounded-full border px-3 py-1 text-sm font-medium transition-colors"
                      :class="activeSection === sec.heading
                        ? 'bg-blue-700 border-blue-700 text-white'
                        : 'border-neutral-300 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800'"
                      @click="activeSection = sec.heading">
                {{ sec.heading || 'General' }}
                <span :class="activeSection === sec.heading
                        ? 'text-blue-100' : 'text-neutral-400 dark:text-neutral-500'"
                      class="text-xs">({{ sec.qids.length }})</span>
              </button>
              <span class="flex-1"></span>
              <button type="button" class="btn !px-2 !py-1 shrink-0"
                      title="Switch to the compact menu view" @click="toggleSectionView">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round">
                  <path d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>

            <!-- compact: hamburger on the left + up to three tabs -->
            <div v-else class="flex items-center gap-1 px-3
                               border-b border-neutral-200 dark:border-neutral-800">
              <div v-if="suggestedSections.length > MAX_SECTION_TABS"
                   ref="sectionMenuRoot" class="relative">
                <button type="button" class="tab !px-2" :aria-expanded="sectionMenuOpen"
                        title="All headings" @click="sectionMenuOpen = !sectionMenuOpen">
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                       stroke-width="2" stroke-linecap="round">
                    <path d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
                <div v-if="sectionMenuOpen"
                     class="absolute left-0 mt-1 w-60 card shadow-lg py-1 z-20 max-h-72 overflow-y-auto">
                  <button v-for="sec in suggestedSections" :key="sec.heading" type="button"
                          class="block w-full text-left px-3 py-1.5 text-sm
                                 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                          :class="activeSection === sec.heading
                            && 'font-semibold text-blue-700 dark:text-blue-400'"
                          @click="activeSection = sec.heading; sectionMenuOpen = false">
                    {{ sec.heading || 'General' }}
                    <span class="text-xs text-neutral-400 dark:text-neutral-500">
                      ({{ sec.qids.length }})</span>
                  </button>
                </div>
              </div>
              <button v-for="sec in visibleSections" :key="sec.heading" type="button"
                      class="tab" :class="{ 'tab-active': activeSection === sec.heading }"
                      @click="activeSection = sec.heading">
                {{ sec.heading || 'General' }}
                <span class="text-xs text-neutral-400 dark:text-neutral-500">({{ sec.qids.length }})</span>
              </button>
              <span class="flex-1"></span>
              <button type="button" class="btn !px-2 !py-1 shrink-0"
                      title="Show all headings as buttons" @click="toggleSectionView">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="7" height="7" rx="1" />
                  <rect x="14" y="3" width="7" height="7" rx="1" />
                  <rect x="3" y="14" width="7" height="7" rx="1" />
                  <rect x="14" y="14" width="7" height="7" rx="1" />
                </svg>
              </button>
            </div>
          </template>
          <!-- loading: this heading's sitelinks are being resolved -->
          <div v-if="activeSectionLoading" class="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300 p-4">
            <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Checking Wikidata and Wikipedia for this tab…
          </div>

          <!-- error: fall back to plain QID links for this heading -->
          <div v-else-if="activeSectionFailed" class="p-4 space-y-2">
            <p class="text-xs text-red-600 dark:text-red-400">
              Could not check article coverage for this tab. Showing the raw items instead.
            </p>
            <div class="flex flex-wrap gap-1.5">
              <a v-for="qid in (suggestedSections.find(s => s.heading === activeSection)?.qids || [])"
                 :key="qid" target="_blank" :href="`https://www.wikidata.org/wiki/${qid}`"
                 class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300 hover:underline">{{ qid }}</a>
            </div>
          </div>

          <template v-else>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-neutral-200 dark:border-neutral-800">
                    <th class="th pl-4">Item</th>
                    <th class="th">Label (English)</th>
                    <th v-for="lang in suggestedLangs" :key="lang" class="th text-center">
                      {{ lang }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in shownSectionItems" :key="item.qid"
                      class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                    <td class="td pl-4">
                      <a :href="`https://www.wikidata.org/wiki/${item.qid}`" target="_blank"
                         class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300 hover:underline">
                        {{ item.qid }}
                      </a>
                    </td>
                    <td class="td font-medium">{{ item.label_en || item.label || '—' }}</td>
                    <td v-for="lang in suggestedLangs" :key="lang" class="td text-center">
                      <!-- exists: link to the article -->
                      <a v-if="itemLink(item, lang)" :href="itemLink(item, lang).url"
                         target="_blank" :title="`${itemLink(item, lang).title} — read on ${lang}.wikipedia.org`"
                         class="inline-flex items-center justify-center w-6 h-6 rounded-full
                                bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300
                                hover:ring-2 hover:ring-green-400">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                          <path d="m5 13 4 4L19 7" />
                        </svg>
                      </a>
                      <!-- missing: start it -->
                      <a v-else :href="createUrl(item, lang)" target="_blank"
                         :title="`Not on ${lang}.wikipedia.org yet — start this article`"
                         class="inline-flex items-center justify-center w-6 h-6 rounded-full
                                bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400
                                hover:bg-blue-100 hover:text-blue-700 dark:hover:bg-blue-950 dark:hover:text-blue-300">
                          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                               stroke-width="3" stroke-linecap="round">
                            <path d="M12 5v14m-7-7h14" />
                          </svg>
                        </a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="text-xs text-neutral-500 dark:text-neutral-400 px-4 py-3">
              ✓ the article exists — click to read it; + it is missing — click to
              start it. Language columns come from
              <router-link to="/preferences" class="text-blue-600 dark:text-blue-400 hover:underline">
                your preferred languages</router-link>.
            </p>
          </template>
        </div>
      </div>
    </div>

    <!-- SUBMISSIONS -->
    <div v-if="tab === 'submissions'">
      <div class="flex flex-wrap items-center gap-x-5 gap-y-2 mb-2">
        <label v-if="auth.isLoggedIn" class="flex items-center gap-2 text-sm cursor-pointer">
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
        <span v-if="filterUser" class="text-xs text-neutral-600 dark:text-neutral-300">
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
             @click="expanded = expanded === s.id ? null : s.id">
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
              <template v-if="s.is_new_page"> · new page</template>
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
          </div>
          <span v-if="s.status !== 'submitted'" class="badge" :class="statusStyles[s.status === 'accepted' ? 'active' : 'rejected']">
            {{ s.status }}
          </span>
          <span class="font-bold tabular-nums text-lg">{{ s.points }}<span class="text-xs font-normal text-neutral-600 dark:text-neutral-300"> pts</span></span>
        </div>

        <div v-if="expanded === s.id" class="border-t border-neutral-100 dark:border-neutral-800 p-3 space-y-4">
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
            <table class="w-full text-sm">
              <tbody>
                <tr v-for="(line, i) in s.breakdown" :key="i"
                    class="border-t border-neutral-100 dark:border-neutral-800 first:border-0">
                  <td class="td pl-0">{{ line.label }}</td>
                  <td class="td text-xs text-neutral-600 dark:text-neutral-300">{{ line.source }}<template v-if="line.status"> · {{ line.status }}</template></td>
                  <td class="td pr-0 text-right tabular-nums">{{ line.points }}</td>
                </tr>
              </tbody>
            </table>
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
                <button class="btn !py-0.5 !px-2 text-xs" @click="moderateClaim(c, 'verified')">Verify</button>
                <button class="btn !py-0.5 !px-2 text-xs" @click="moderateClaim(c, 'adjusted')">Adjust</button>
                <button class="btn-danger !py-0.5 !px-2 text-xs" @click="moderateClaim(c, 'rejected')">Reject</button>
              </template>
            </div>
          </div>

          <!-- claim editor for the owner -->
          <div v-if="selfMode && auth.user?.username === s.user.username && campaign.status !== 'archived'">
            <h5 class="label">Claim your points</h5>
            <ClaimEditor :rules="campaign.rules" :submission="s" @save="claims => saveClaims(s, claims)" />
          </div>

          <!-- review form for jurors -->
          <div v-if="isJury && campaign.scoring_mode !== 'self' && auth.user?.username !== s.user.username && campaign.status !== 'archived'">
            <h5 class="label">Your review</h5>
            <ReviewForm :criteria="criteria"
                        :existing="s.reviews.find(r => r.reviewer.username === auth.user?.username)"
                        @save="review => saveReview(s, review)" />
          </div>

          <!-- actions -->
          <div class="flex flex-wrap gap-2 pt-1">
            <button class="btn" @click="refresh(s)">Refresh wiki data</button>
            <button v-if="auth.user?.username === s.user.username && campaign.status === 'active'"
                    class="btn-danger" @click="withdraw(s)">Withdraw</button>
            <template v-if="isOrganizer">
              <button class="btn" @click="moderateSub(s, 'accepted')">Accept</button>
              <button class="btn-danger" @click="moderateSub(s, 'rejected')">Reject</button>
              <button class="btn" @click="overrideSub(s)">Override points</button>
              <button class="btn" title="Refetch wiki data and rescore from the campaign rules, clearing any override"
                      @click="recalculate(s)">Recalculate points</button>
            </template>
          </div>
        </div>
      </div>
        </div>
      </div>
    </div>

    <!-- LEADERBOARD -->
    <div v-if="tab === 'leaderboard'">
      <p v-if="!leaderboard.length" class="text-neutral-600 dark:text-neutral-300">No points yet.</p>
      <cdx-table v-else caption="Leaderboard" :hide-caption="true"
                 :columns="lbColumns" :data="lbRows"
                 :sort="lbSort" @update:sort="onLbSort">
        <template #item-username="{ item, row }">
          <button type="button" title="Show this participant's submissions"
                  class="font-medium text-blue-700 dark:text-blue-400 hover:underline"
                  @click="detailsUser = row.user">{{ item }}</button>
        </template>
        <template #item-points="{ item }">
          <span class="tabular-nums font-semibold">{{ item }}</span>
        </template>
      </cdx-table>
    </div>

    <!-- STATISTICS -->
    <StatsTab v-if="tab === 'stats'" :slug="slug" />

    <ParticipantDetails v-if="detailsUser" :slug="slug" :user="detailsUser"
                        @close="detailsUser = null" />
  </div>
</template>
