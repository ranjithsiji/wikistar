<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api, { errorMessage } from '../api'
import AppMessage from '../components/AppMessage.vue'
import UserAvatar from '../components/UserAvatar.vue'

// Full-page admin screen for one campaign. This replaces the inline
// expander that used to live in the Editathons list: the members and
// submissions tables need the whole width, and every view here is
// linkable (/admin/campaigns/<slug>/<panel>).
const props = defineProps({
  slug: { type: String, required: true },
  panel: { type: String, default: '' }
})
const router = useRouter()

const error = ref('')
const busy = ref(false)
const campaign = ref(null)     // full detail (members)
const articles = ref(null)     // submissions, loaded on first visit
const panel = ref(props.panel || 'members')
const newMember = ref({ username: '', role: 'jury' })

const STATUS_BADGE = {
  draft: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  active: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  finished: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  archived: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
}

const PANELS = [['members', 'Members'], ['articles', 'Articles']]

// Review-state filter for the submissions table. "Awaiting my review" is
// deliberately absent: an admin working across campaigns has no personal
// review queue here — these are the campaign-wide backlogs.
const REVIEW_FILTERS = [
  ['unreviewed', 'Not reviewed by anyone'],
  ['not_accepted', 'Not accepted yet'],
  ['rejected', 'Rejected']
]
const REVIEW_TESTS = {
  // A rejected submission is already decided, so it is not a backlog.
  unreviewed: (s) => s.status !== 'rejected' && !s.reviews.length,
  not_accepted: (s) => s.status === 'submitted',
  rejected: (s) => s.status === 'rejected'
}
const filterReview = ref('')
const searchArticles = ref('')
// Set from the members table ("show submissions"), and from the article
// search box when it matches a participant.
const filterMember = ref('')

const normalize = (s) => (s || '').toString().toLowerCase().trim()

// Participants who actually submitted something, for the member filter.
const articleAuthors = computed(() => [...new Set(
  (articles.value || []).map(s => s.user.username))].sort(
  (a, b) => a.localeCompare(b)))

const shownArticles = computed(() => {
  let list = articles.value || []
  const test = REVIEW_TESTS[filterReview.value]
  if (test) list = list.filter(test)
  if (filterMember.value) {
    list = list.filter(s => s.user.username === filterMember.value)
  }
  const q = normalize(searchArticles.value)
  if (q) {
    // Title or submitter: an admin looking for "what did X submit" and
    // one looking for a specific page both type into the same box.
    list = list.filter(s => normalize(s.title).includes(q) ||
                            normalize(s.user.username).includes(q))
  }
  return sortRows(list)
})
const reviewCounts = computed(() => Object.fromEntries(
  Object.entries(REVIEW_TESTS).map(([key, test]) =>
    [key, (articles.value || []).filter(test).length])))

// ---- sorting ---------------------------------------------------------------
// Columns the articles table can be ordered by, with the value to compare.
const SORT_KEYS = {
  title: (s) => normalize(s.title),
  user: (s) => normalize(s.user.username),
  kind: (s) => s.kind,
  status: (s) => s.status,
  points: (s) => Number(s.points) || 0,
  submitted_at: (s) => new Date(s.submitted_at).getTime()
}
const sortBy = ref('submitted_at')
const sortDesc = ref(true)   // newest first, matching the API's own order

function toggleSort (key) {
  if (sortBy.value === key) {
    sortDesc.value = !sortDesc.value
  } else {
    sortBy.value = key
    // Numbers and dates are most useful largest-first; text A→Z.
    sortDesc.value = ['points', 'submitted_at'].includes(key)
  }
}

function sortRows (list) {
  const pick = SORT_KEYS[sortBy.value]
  if (!pick) return list
  // toSorted would mutate nothing, but is newer than some of the
  // browsers this tool sees; copy explicitly.
  return [...list].sort((a, b) => {
    const x = pick(a); const y = pick(b)
    if (x < y) return sortDesc.value ? 1 : -1
    if (x > y) return sortDesc.value ? -1 : 1
    return 0
  })
}

function sortIndicator (key) {
  if (sortBy.value !== key) return ''
  return sortDesc.value ? '▾' : '▴'
}

// Bound rather than written out on each header: Tailwind v4 cannot
// resolve @apply inside a scoped <style> block without a @reference,
// and repeating this string six times invites them to drift apart.
const TH_SORT = 'inline-flex items-center gap-1 cursor-pointer select-none ' +
  'hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors'
const SORT_MARK = 'text-xs text-blue-700 dark:text-blue-400 w-2 inline-block'

function ariaSort (key) {
  if (sortBy.value !== key) return 'none'
  return sortDesc.value ? 'descending' : 'ascending'
}

function showMemberArticles (username) {
  filterMember.value = username
  searchArticles.value = ''
  filterReview.value = ''
  selectPanel('articles')
}

function clearArticleFilters () {
  filterMember.value = ''
  searchArticles.value = ''
  filterReview.value = ''
}

const articleFiltersActive = computed(() =>
  !!(filterMember.value || searchArticles.value || filterReview.value))

// ---- members ---------------------------------------------------------------
const searchMembers = ref('')
const shownMembers = computed(() => {
  const all = campaign.value?.members || []
  const q = normalize(searchMembers.value)
  if (!q) return all
  return all.filter(m => normalize(m.user.username).includes(q) ||
                         normalize(m.role).includes(q))
})
// How many submissions each member has, so the members table can offer
// "show submissions" only where there is something to show.
const submissionsByUser = computed(() => {
  const counts = {}
  for (const s of articles.value || []) {
    counts[s.user.username] = (counts[s.user.username] || 0) + 1
  }
  return counts
})

const memberCount = computed(() => campaign.value?.members?.length ?? 0)

async function run (fn) {
  busy.value = true
  error.value = ''
  try { await fn() } catch (e) { error.value = errorMessage(e) } finally { busy.value = false }
}

async function loadCampaign () {
  await run(async () => { campaign.value = (await api.getCampaign(props.slug)).data })
}
async function loadArticles () {
  if (articles.value) return
  await run(async () => { articles.value = (await api.listSubmissions(props.slug)).data })
}
async function reloadArticles () {
  articles.value = (await api.listSubmissions(props.slug)).data
}

onMounted(async () => {
  await loadCampaign()
  // Both panels need them: the members table shows each member's
  // submission count and links through to them.
  await loadArticles()
})

function selectPanel (key) {
  panel.value = key
  router.push(`/admin/campaigns/${props.slug}/${key}`)
  if (key === 'articles') loadArticles()
}

// Browser back/forward, or a direct link to a specific panel.
watch(() => props.panel, (key) => {
  const next = key || 'members'
  if (next !== panel.value) {
    panel.value = next
    if (next === 'articles') loadArticles()
  }
})

// ---- campaign-level actions ------------------------------------------------
async function approve () {
  await run(async () => { await api.approveCampaign(props.slug); await loadCampaign() })
}
async function reject () {
  const reason = prompt(`Reject "${campaign.value.name}"? Optional reason:`)
  if (reason === null) return
  await run(async () => { await api.rejectCampaign(props.slug, reason); await loadCampaign() })
}
async function deactivate () {
  if (!confirm(`Deactivate "${campaign.value.name}"? It goes back to draft and is hidden until approved again.`)) return
  await run(async () => { await api.deactivateCampaign(props.slug); await loadCampaign() })
}
async function removeCampaign () {
  if (!confirm(`Delete campaign "${campaign.value.name}" with all its submissions? This cannot be undone.`)) return
  await run(async () => {
    await api.deleteCampaign(props.slug)
    router.push('/admin/campaigns')
  })
}

// ---- members ---------------------------------------------------------------
async function addMember () {
  const username = newMember.value.username.trim()
  if (!username) return
  await run(async () => {
    campaign.value = (await api.addMember(props.slug, {
      username, role: newMember.value.role
    })).data
    newMember.value.username = ''
  })
}
async function removeMember (m) {
  if (!confirm(`Remove ${m.user.username} (${m.role}) from this campaign?`)) return
  await run(async () => {
    campaign.value = (await api.removeMember(props.slug, m.id)).data
  })
}

// ---- submitted articles: admin repairs -------------------------------------
// Edit dialog. A prompt() could only ever change one field and gave no
// way to see what was being corrected, so title, wiki and the
// moderation note are edited together against the submission's row.
const editing = ref(null)   // { id, title, wiki_domain, moderation_note, original }

function onEditKeydown (e) {
  if (e.key === 'Escape' && editing.value) cancelEdit()
}
onMounted(() => window.addEventListener('keydown', onEditKeydown))
onUnmounted(() => window.removeEventListener('keydown', onEditKeydown))

function startEdit (s) {
  editing.value = {
    id: s.id,
    title: s.title,
    wiki_domain: s.wiki_domain,
    moderation_note: s.moderation_note || '',
    original: s
  }
}
function cancelEdit () { editing.value = null }

const editDirty = computed(() => {
  const e = editing.value
  if (!e) return false
  return e.title.trim() !== e.original.title ||
         e.wiki_domain.trim() !== e.original.wiki_domain ||
         e.moderation_note.trim() !== (e.original.moderation_note || '')
})

async function saveEdit () {
  const e = editing.value
  if (!e || !e.title.trim()) return
  await run(async () => {
    await api.adminEditSubmission(e.id, {
      title: e.title.trim(),
      wiki_domain: e.wiki_domain.trim(),
      moderation_note: e.moderation_note.trim()
    })
    await reloadArticles()
    editing.value = null
  })
}
async function moderateArticle (s, status) {
  await run(async () => {
    await api.moderateSubmission(s.id, { status })
    await reloadArticles()
  })
}
async function overrideArticle (s) {
  const v = prompt('Final points (empty to clear the override):', s.points_override ?? '')
  if (v === null) return
  const payload = v === '' ? { clear_override: true } : { points_override: Number(v) }
  await run(async () => {
    await api.moderateSubmission(s.id, payload)
    await reloadArticles()
  })
}
async function deleteArticle (s) {
  if (!confirm(`Delete the submission "${s.title}" by ${s.user.username}?`)) return
  await run(async () => {
    await api.deleteSubmission(s.id)
    await reloadArticles()
  })
}
</script>

<template>
  <div class="admin-shell">
    <div class="flex items-center gap-3 flex-wrap">
      <router-link to="/admin/campaigns"
                   class="text-sm text-link-700 dark:text-link-400 hover:underline">
        ← Back to Editathons
      </router-link>
      <span class="admin-chip">Admin area</span>
    </div>

    <AppMessage v-model="error" type="error" class="mt-3" />

    <p v-if="!campaign" class="text-sm text-neutral-600 dark:text-neutral-300 mt-4">Loading…</p>

    <template v-else>
      <div class="flex items-center gap-3 flex-wrap mt-2 mb-1">
        <h1 class="text-2xl font-bold">{{ campaign.name }}</h1>
        <span class="badge" :class="STATUS_BADGE[campaign.status]">{{ campaign.status }}</span>
      </div>
      <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
        by {{ campaign.created_by_username || '—' }} ·
        {{ campaign.start_date }} → {{ campaign.end_date }} ·
        {{ campaign.submission_count }} submissions · {{ campaign.participant_count }} participants
      </p>

      <div class="flex gap-2 flex-wrap mb-5">
        <router-link class="btn" :to="`/campaigns/${slug}`">View campaign</router-link>
        <router-link class="btn" :to="`/campaigns/${slug}/edit`">Edit settings</router-link>
        <button v-if="['draft', 'rejected'].includes(campaign.status)" class="btn-primary"
                :disabled="busy" @click="approve">Approve</button>
        <button v-if="campaign.status === 'draft'" class="btn"
                :disabled="busy" @click="reject">Reject</button>
        <button v-if="campaign.status === 'active'" class="btn"
                :disabled="busy" @click="deactivate">Deactivate</button>
        <button class="btn-danger" :disabled="busy" @click="removeCampaign">Delete</button>
      </div>

      <div class="tab-group w-fit max-w-full overflow-x-auto">
        <button v-for="[key, label] in PANELS" :key="key" class="tab"
                :class="{ 'tab-active': panel === key }" @click="selectPanel(key)">
          {{ label }}
          <span v-if="key === 'members' && memberCount"
                class="badge bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300 ml-1">
            {{ memberCount }}
          </span>
        </button>
      </div>

      <div class="tab-panel p-4">

        <!-- ============================ Members ============================ -->
        <div v-if="panel === 'members'">
          <label v-if="campaign.members.length" class="flex items-center gap-2 text-sm mb-3 flex-wrap">
            <input v-model="searchMembers" type="search" class="input !w-64 !py-1"
                   placeholder="Search members by name or role…" />
            <span v-if="searchMembers" class="text-xs text-neutral-600 dark:text-neutral-300">
              {{ shownMembers.length }} of {{ campaign.members.length }}
            </span>
          </label>
          <div class="overflow-x-auto mb-3">
            <table class="w-full">
              <thead>
                <tr class="border-b border-neutral-200 dark:border-neutral-800">
                  <th class="th">User</th><th class="th">Role</th>
                  <th class="th text-right">Submissions</th>
                  <th class="th text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!campaign.members.length">
                  <td class="td text-sm text-neutral-600 dark:text-neutral-300" colspan="4">
                    No members yet.
                  </td>
                </tr>
                <tr v-else-if="!shownMembers.length">
                  <td class="td text-sm text-neutral-600 dark:text-neutral-300" colspan="4">
                    No members match “{{ searchMembers }}”.
                  </td>
                </tr>
                <tr v-for="m in shownMembers" :key="m.id"
                    class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                  <td class="td">
                    <span class="inline-flex items-center gap-2">
                      <UserAvatar :username="m.user.username" size="sm" />
                      {{ m.user.username }}
                    </span>
                  </td>
                  <td class="td">
                    <span class="badge bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                      {{ m.role }}
                    </span>
                  </td>
                  <td class="td text-right tabular-nums text-sm">
                    <button v-if="submissionsByUser[m.user.username]"
                            class="text-link-700 dark:text-link-400 hover:underline cursor-pointer"
                            title="Show this member's submissions"
                            @click="showMemberArticles(m.user.username)">
                      {{ submissionsByUser[m.user.username] }}
                    </button>
                    <span v-else class="text-neutral-500 dark:text-neutral-400">—</span>
                  </td>
                  <td class="td text-right">
                    <button class="btn-danger !py-0.5 !px-2 text-xs" :disabled="busy"
                            @click="removeMember(m)">remove</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <form class="flex gap-2 items-center flex-wrap" @submit.prevent="addMember">
            <input v-model="newMember.username" class="input !w-56" placeholder="Wikimedia username" />
            <select v-model="newMember.role" class="input !w-36">
              <option value="participant">participant</option>
              <option value="jury">jury</option>
              <option value="organizer">organizer</option>
            </select>
            <button class="btn-primary" :disabled="busy || !newMember.username.trim()">
              Add member
            </button>
          </form>
        </div>

        <!-- =========================== Articles ============================ -->
        <div v-if="panel === 'articles'">
          <p v-if="!articles" class="text-sm text-neutral-600 dark:text-neutral-300">Loading…</p>
          <p v-else-if="!articles.length" class="text-sm text-neutral-600 dark:text-neutral-300">
            No submissions yet.
          </p>
          <template v-else>
          <div class="flex items-end gap-3 mb-3 flex-wrap">
            <label class="text-sm">
              <span class="block text-xs text-neutral-600 dark:text-neutral-300 mb-1">
                Search
              </span>
              <input v-model="searchArticles" type="search" class="input !w-72 !py-1"
                     placeholder="Article title or member name…" />
            </label>
            <label class="text-sm">
              <span class="block text-xs text-neutral-600 dark:text-neutral-300 mb-1">
                Member
              </span>
              <select v-model="filterMember" class="input !w-48 !py-1">
                <option value="">All members</option>
                <option v-for="name in articleAuthors" :key="name" :value="name">
                  {{ name }}
                </option>
              </select>
            </label>
            <label class="text-sm">
              <span class="block text-xs text-neutral-600 dark:text-neutral-300 mb-1">
                Review state
              </span>
              <select v-model="filterReview" class="input !w-56 !py-1">
                <option value="">All submissions</option>
                <option v-for="[key, label] in REVIEW_FILTERS" :key="key" :value="key"
                        :disabled="!reviewCounts[key]">
                  {{ label }} ({{ reviewCounts[key] }})
                </option>
              </select>
            </label>
            <button v-if="articleFiltersActive" class="btn !py-1 !px-2 text-xs"
                    @click="clearArticleFilters">Clear filters</button>
            <span v-if="articleFiltersActive"
                  class="text-xs text-neutral-600 dark:text-neutral-300 pb-2">
              {{ shownArticles.length }} of {{ articles.length }} submissions
            </span>
          </div>
          <p v-if="!shownArticles.length" class="text-sm text-neutral-600 dark:text-neutral-300">
            No submissions match these filters.
          </p>
          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-neutral-200 dark:border-neutral-800">
                  <th class="th">
                    <button :class="[TH_SORT]" @click="toggleSort('title')"
                            :aria-sort="ariaSort('title')">
                      Title <span :class="SORT_MARK">{{ sortIndicator('title') }}</span>
                    </button>
                  </th>
                  <th class="th">
                    <button :class="[TH_SORT]" @click="toggleSort('user')"
                            :aria-sort="ariaSort('user')">
                      User <span :class="SORT_MARK">{{ sortIndicator('user') }}</span>
                    </button>
                  </th>
                  <th class="th">
                    <button :class="[TH_SORT]" @click="toggleSort('kind')"
                            :aria-sort="ariaSort('kind')">
                      Kind <span :class="SORT_MARK">{{ sortIndicator('kind') }}</span>
                    </button>
                  </th>
                  <th class="th">
                    <button :class="[TH_SORT]" @click="toggleSort('status')"
                            :aria-sort="ariaSort('status')">
                      Status <span :class="SORT_MARK">{{ sortIndicator('status') }}</span>
                    </button>
                  </th>
                  <th class="th text-right">
                    <button :class="[TH_SORT, 'justify-end w-full']" @click="toggleSort('points')"
                            :aria-sort="ariaSort('points')">
                      Points <span :class="SORT_MARK">{{ sortIndicator('points') }}</span>
                    </button>
                  </th>
                  <th class="th">
                    <button :class="[TH_SORT]" @click="toggleSort('submitted_at')"
                            :aria-sort="ariaSort('submitted_at')">
                      Submitted <span :class="SORT_MARK">{{ sortIndicator('submitted_at') }}</span>
                    </button>
                  </th>
                  <th class="th text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in shownArticles" :key="s.id"
                    class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                  <td class="td">
                    <a :href="s.url" target="_blank" rel="noopener"
                       class="text-link-700 dark:text-link-400 hover:underline">{{ s.title }}</a>
                    <span class="block text-xs text-neutral-500 dark:text-neutral-400">
                      {{ s.wiki_domain }}
                    </span>
                  </td>
                  <td class="td">
                    <button class="text-link-700 dark:text-link-400 hover:underline cursor-pointer"
                            title="Show only this member's submissions"
                            @click="showMemberArticles(s.user.username)">
                      {{ s.user.username }}
                    </button>
                  </td>
                  <td class="td text-xs text-neutral-600 dark:text-neutral-300">{{ s.kind }}</td>
                  <td class="td text-xs">
                    {{ s.status }}
                    <span v-if="s.points_override != null"
                          class="badge bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                          title="Points manually overridden">override</span>
                  </td>
                  <td class="td text-right tabular-nums">{{ s.points }}</td>
                  <td class="td text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap">
                    {{ new Date(s.submitted_at).toLocaleDateString() }}
                  </td>
                  <td class="td text-right whitespace-nowrap space-x-1">
                    <button class="btn !py-0.5 !px-2 text-xs" :disabled="busy"
                            title="Fix the title, wiki or moderation note"
                            @click="startEdit(s)">Edit</button>
                    <button class="btn !py-0.5 !px-2 text-xs" :disabled="busy"
                            @click="moderateArticle(s, 'accepted')">Accept</button>
                    <button class="btn !py-0.5 !px-2 text-xs" :disabled="busy"
                            @click="moderateArticle(s, 'rejected')">Reject</button>
                    <button class="btn !py-0.5 !px-2 text-xs" :disabled="busy"
                            title="Set or clear a manual points override" @click="overrideArticle(s)">Points</button>
                    <button class="btn-danger !py-0.5 !px-2 text-xs" :disabled="busy"
                            @click="deleteArticle(s)">Delete</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          </template>
        </div>
      </div>
    </template>

    <!-- ===================== Edit submission dialog ===================== -->
    <div v-if="editing"
         class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
         @click.self="cancelEdit">
      <div class="card w-full max-w-lg p-5 shadow-xl" role="dialog" aria-modal="true"
           aria-labelledby="edit-submission-title">
        <h2 id="edit-submission-title" class="text-lg font-bold mb-1">Edit submission</h2>
        <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
          by {{ editing.original.user.username }}
        </p>

        <form @submit.prevent="saveEdit">
          <label class="block mb-3">
            <span class="label">Page title</span>
            <input v-model="editing.title" class="input" required
                   placeholder="Exactly as it appears on the wiki" />
          </label>
          <label class="block mb-3">
            <span class="label">Wiki</span>
            <input v-model="editing.wiki_domain" class="input"
                   placeholder="ml.wikipedia.org" />
            <span class="block text-xs text-neutral-600 dark:text-neutral-300 mt-1">
              Changing the title or wiki refetches the page's metadata, so
              bytes added and points follow the correction.
            </span>
          </label>
          <label class="block mb-4">
            <span class="label">Moderation note</span>
            <textarea v-model="editing.moderation_note" class="input" rows="2"
                      placeholder="Shown to the participant next to the status"></textarea>
          </label>

          <div class="flex gap-2 justify-end">
            <button type="button" class="btn" @click="cancelEdit">Cancel</button>
            <button type="submit" class="btn-primary"
                    :disabled="busy || !editing.title.trim() || !editDirty">
              Save changes
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
