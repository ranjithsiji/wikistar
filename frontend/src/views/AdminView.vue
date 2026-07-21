<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api, { errorMessage } from '../api'
import AppMessage from '../components/AppMessage.vue'
import { useAuthStore } from '../store'

const auth = useAuthStore()
const error = ref('')

const TABS = [
  ['dashboard', 'Dashboard'],
  ['campaigns', 'Editathons'],
  ['users', 'Users'],
  ['activity', 'Activity log'],
]
const tab = ref('dashboard')

// ---- dashboard -------------------------------------------------------------
const stats = ref(null)

// ---- editathons ------------------------------------------------------------
const campaigns = ref([])
const statusFilter = ref('all')
const shownCampaigns = computed(() =>
  statusFilter.value === 'all'
    ? campaigns.value
    : campaigns.value.filter(c => c.status === statusFilter.value))
const expanded = ref(null)          // slug of the expanded campaign row
const detail = ref(null)            // campaign detail (members) of expanded row
const articles = ref(null)          // submissions of expanded row
const panel = ref('members')        // 'members' | 'articles'
const newMember = ref({ username: '', role: 'jury' })
const busy = ref(false)

const pendingCampaigns = computed(() =>
  campaigns.value.filter(c => c.status === 'draft'))

const STATUS_BADGE = {
  draft: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  active: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  finished: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  archived: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
}

// ---- users -----------------------------------------------------------------
const users = ref([])
const userFilter = ref('')
const filteredUsers = computed(() => {
  const q = userFilter.value.trim().toLowerCase()
  return q ? users.value.filter(u => u.username.toLowerCase().includes(q)) : users.value
})

// ---- activity --------------------------------------------------------------
const logs = ref({ total: 0, logs: [], actions: [] })
const logAction = ref('')
const logUser = ref('')
let logTimer = null

const logParams = () => ({
  limit: 100,
  ...(logAction.value ? { action: logAction.value } : {}),
  ...(logUser.value.trim() ? { username: logUser.value.trim() } : {})
})

async function reloadLogs () {
  try {
    logs.value = (await api.adminLogs(logParams())).data
  } catch (e) { error.value = errorMessage(e) }
}
watch(logAction, reloadLogs)
watch(logUser, () => {
  clearTimeout(logTimer)
  logTimer = setTimeout(reloadLogs, 300)
})

async function load () {
  error.value = ''
  try {
    const [s, u, l, c] = await Promise.all([
      api.adminStats(), api.adminUsers(), api.adminLogs({ limit: 100 }), api.adminCampaigns()
    ])
    stats.value = s.data
    users.value = u.data
    logs.value = l.data
    campaigns.value = c.data
  } catch (e) {
    error.value = errorMessage(e)
  }
}
onMounted(load)

async function loadMoreLogs () {
  try {
    const { data } = await api.adminLogs(
      { ...logParams(), offset: logs.value.logs.length })
    logs.value = { ...data, logs: [...logs.value.logs, ...data.logs] }
  } catch (e) { error.value = errorMessage(e) }
}

async function toggleAdmin (u) {
  try {
    await api.setAdmin(u.id, !u.is_admin)
    const { data } = await api.adminUsers()
    users.value = data
  } catch (e) { error.value = errorMessage(e) }
}

// ---- editathon actions -------------------------------------------------------
async function run (fn) {
  busy.value = true
  error.value = ''
  try { await fn() } catch (e) { error.value = errorMessage(e) } finally { busy.value = false }
}

async function toggleExpand (c) {
  if (expanded.value === c.slug) { expanded.value = null; return }
  expanded.value = c.slug
  panel.value = 'members'
  detail.value = null
  articles.value = null
  await run(async () => { detail.value = (await api.getCampaign(c.slug)).data })
}

async function showArticles () {
  panel.value = 'articles'
  if (articles.value) return
  await run(async () => { articles.value = (await api.listSubmissions(expanded.value)).data })
}

async function addMember () {
  const username = newMember.value.username.trim()
  if (!username) return
  await run(async () => {
    detail.value = (await api.addMember(expanded.value, {
      username, role: newMember.value.role
    })).data
    newMember.value.username = ''
  })
}

async function removeMember (m) {
  if (!confirm(`Remove ${m.user.username} (${m.role}) from this campaign?`)) return
  await run(async () => {
    detail.value = (await api.removeMember(expanded.value, m.id)).data
  })
}

async function approve (c) {
  await run(async () => { await api.approveCampaign(c.slug); await refreshCampaigns() })
}
async function reject (c) {
  const reason = prompt(`Reject "${c.name}"? Optional reason:`)
  if (reason === null) return
  await run(async () => { await api.rejectCampaign(c.slug, reason); await refreshCampaigns() })
}
async function removeCampaign (c) {
  if (!confirm(`Delete campaign "${c.name}" with all its submissions? This cannot be undone.`)) return
  await run(async () => {
    await api.deleteCampaign(c.slug)
    if (expanded.value === c.slug) expanded.value = null
    await refreshCampaigns()
  })
}
async function deactivate (c) {
  if (!confirm(`Deactivate "${c.name}"? It goes back to draft and is hidden until approved again.`)) return
  await run(async () => { await api.deactivateCampaign(c.slug); await refreshCampaigns() })
}
async function refreshCampaigns () {
  campaigns.value = (await api.adminCampaigns()).data
  const { data } = await api.adminStats()
  stats.value = data
}

// ---- submitted articles: admin repairs -------------------------------------
async function reloadArticles () {
  articles.value = (await api.listSubmissions(expanded.value)).data
}
async function renameArticle (s) {
  const title = prompt('New title for this submission:', s.title)
  if (title === null || !title.trim() || title.trim() === s.title) return
  await run(async () => {
    await api.adminEditSubmission(s.id, { title: title.trim() })
    await reloadArticles()
  })
}
async function moderateArticle (s, status) {
  await run(async () => {
    await api.moderateSubmission(s.id, { status })
    await reloadArticles()
  })
}
async function overrideArticle (s) {
  const v = prompt('Final points (empty to clear the override):',
                   s.points_override ?? '')
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
  <div>
    <h1 class="text-2xl font-bold mb-4">Administration</h1>
    <AppMessage v-model="error" type="error" />

    <div class="flex gap-1 border-b border-neutral-200 dark:border-neutral-800 mb-5 overflow-x-auto">
      <button v-for="[key, label] in TABS" :key="key" class="tab"
              :class="{ 'tab-active': tab === key }" @click="tab = key">
        {{ label }}
        <span v-if="key === 'dashboard' && pendingCampaigns.length"
              class="badge bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 ml-1">
          {{ pendingCampaigns.length }}
        </span>
      </button>
    </div>

    <!-- =========================== Dashboard =========================== -->
    <div v-if="tab === 'dashboard'">
      <div v-if="stats" class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
        <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.users }}</div><div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">Users</div></div>
        <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.campaigns }}</div><div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">Editathons</div></div>
        <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.active_campaigns }}</div><div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">Active</div></div>
        <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.pending_campaigns }}</div><div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">Pending approval</div></div>
        <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.submissions }}</div><div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">Submissions</div></div>
        <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.reviews }}</div><div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">Reviews</div></div>
        <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.claims }}</div><div class="text-xs text-neutral-600 dark:text-neutral-300 mt-1">Claims</div></div>
      </div>

      <h2 class="font-semibold mb-2">Editathons awaiting approval</h2>
      <p v-if="!pendingCampaigns.length" class="text-sm text-neutral-600 dark:text-neutral-300">
        Nothing waiting for approval.
      </p>
      <div v-for="c in pendingCampaigns" :key="c.id" class="card p-3 mb-2 flex items-center gap-3 flex-wrap">
        <router-link :to="`/campaigns/${c.slug}`" class="font-medium text-blue-700 dark:text-blue-400 hover:underline flex-1 min-w-40">
          {{ c.name }}
        </router-link>
        <span class="text-xs text-neutral-600 dark:text-neutral-300">by {{ c.created_by_username || '—' }}</span>
        <span class="text-xs text-neutral-600 dark:text-neutral-300">{{ c.start_date }} → {{ c.end_date }}</span>
        <button class="btn" :disabled="busy" @click="reject(c)">Reject</button>
        <button class="btn-primary" :disabled="busy" @click="approve(c)">Approve</button>
      </div>

      <h2 class="font-semibold mb-2 mt-6">Latest activity</h2>
      <div class="card overflow-x-auto">
        <table class="w-full">
          <tbody>
            <tr v-for="l in logs.logs.slice(0, 10)" :key="l.id"
                class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
              <td class="td text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap">{{ new Date(l.created_at).toLocaleString() }}</td>
              <td class="td">{{ l.username }}</td>
              <td class="td">{{ l.action }}</td>
              <td class="td text-xs text-neutral-600 dark:text-neutral-300">{{ l.entity_type }} {{ l.details?.title || l.details?.username || l.details?.slug || l.entity_id || '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- =========================== Editathons ========================== -->
    <div v-if="tab === 'campaigns'" class="space-y-2">
      <div class="flex gap-1 mb-1">
        <button v-for="f in ['all', 'draft', 'active', 'finished', 'archived', 'rejected']"
                :key="f" class="tab !py-1" :class="{ 'tab-active': statusFilter === f }"
                @click="statusFilter = f">{{ f }}</button>
      </div>
      <div v-for="c in shownCampaigns" :key="c.id" class="card">
        <div class="p-3 flex items-center gap-3 flex-wrap">
          <button class="btn !px-2 !py-0.5 text-xs" @click="toggleExpand(c)">
            {{ expanded === c.slug ? '▾' : '▸' }}
          </button>
          <router-link :to="`/campaigns/${c.slug}`"
                       class="font-medium text-blue-700 dark:text-blue-400 hover:underline flex-1 min-w-40 truncate">
            {{ c.name }}
          </router-link>
          <span class="badge" :class="STATUS_BADGE[c.status]">{{ c.status }}</span>
          <span class="text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap">by {{ c.created_by_username || '—' }}</span>
          <span class="text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap">{{ c.start_date }} → {{ c.end_date }}</span>
          <span class="text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap tabular-nums"
                :title="`${c.submission_count} submissions / ${c.participant_count} participants`">
            {{ c.submission_count }} subs · {{ c.participant_count }} users
          </span>
          <button v-if="['draft', 'rejected'].includes(c.status)" class="btn-primary !py-0.5 text-xs"
                  :disabled="busy" @click="approve(c)">Approve</button>
          <button v-if="c.status === 'draft'" class="btn !py-0.5 text-xs"
                  :disabled="busy" @click="reject(c)">Reject</button>
          <button v-if="c.status === 'active'" class="btn !py-0.5 text-xs"
                  :disabled="busy" @click="deactivate(c)">Deactivate</button>
          <button class="btn-danger !py-0.5 text-xs" :disabled="busy" @click="removeCampaign(c)">Delete</button>
        </div>

        <div v-if="expanded === c.slug" class="border-t border-neutral-200 dark:border-neutral-800 p-4">
          <div class="flex gap-1 mb-3">
            <button class="tab !py-1" :class="{ 'tab-active': panel === 'members' }"
                    @click="panel = 'members'">Members</button>
            <button class="tab !py-1" :class="{ 'tab-active': panel === 'articles' }"
                    @click="showArticles">Articles</button>
          </div>

          <!-- members panel -->
          <div v-if="panel === 'members'">
            <p v-if="!detail" class="text-sm text-neutral-600 dark:text-neutral-300">Loading…</p>
            <template v-else>
              <table class="w-full max-w-2xl mb-3">
                <tbody>
                  <tr v-for="m in detail.members" :key="m.id"
                      class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                    <td class="td">{{ m.user.username }}</td>
                    <td class="td"><span class="badge bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">{{ m.role }}</span></td>
                    <td class="td text-right">
                      <button class="btn-danger !py-0.5 !px-2 text-xs" :disabled="busy"
                              @click="removeMember(m)">remove</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <form class="flex gap-2 items-center flex-wrap" @submit.prevent="addMember">
                <input v-model="newMember.username" class="input !w-56"
                       placeholder="Wikimedia username" />
                <select v-model="newMember.role" class="input !w-36">
                  <option value="participant">participant</option>
                  <option value="jury">jury</option>
                  <option value="organizer">organizer</option>
                </select>
                <button class="btn-primary" :disabled="busy || !newMember.username.trim()">
                  Add member
                </button>
              </form>
            </template>
          </div>

          <!-- articles panel -->
          <div v-if="panel === 'articles'">
            <p v-if="!articles" class="text-sm text-neutral-600 dark:text-neutral-300">Loading…</p>
            <p v-else-if="!articles.length" class="text-sm text-neutral-600 dark:text-neutral-300">No submissions yet.</p>
            <div v-else class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-neutral-200 dark:border-neutral-800">
                    <th class="th">Title</th><th class="th">User</th><th class="th">Kind</th>
                    <th class="th">Status</th><th class="th text-right">Points</th><th class="th">Submitted</th>
                    <th class="th text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in articles" :key="s.id"
                      class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                    <td class="td">
                      <a :href="s.url" target="_blank" rel="noopener"
                         class="text-blue-700 dark:text-blue-400 hover:underline">{{ s.title }}</a>
                    </td>
                    <td class="td">{{ s.user.username }}</td>
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
                              title="Rename the submitted page" @click="renameArticle(s)">Rename</button>
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
          </div>
        </div>
      </div>
    </div>

    <!-- ============================= Users ============================= -->
    <div v-if="tab === 'users'">
      <input v-model="userFilter" class="input !w-64 mb-3" placeholder="Filter users…" />
      <div class="card overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-neutral-200 dark:border-neutral-800">
              <th class="th">Username</th><th class="th">Registered</th>
              <th class="th">Last login</th>
              <th class="th text-right">Submissions</th>
              <th class="th text-right">Campaigns</th>
              <th class="th">Site admin</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in filteredUsers" :key="u.id"
                class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
              <td class="td">
                <a :href="`https://meta.wikimedia.org/wiki/User:${u.username.replaceAll(' ', '_')}`"
                   target="_blank" rel="noopener"
                   class="text-blue-700 dark:text-blue-400 hover:underline">{{ u.username }}</a>
              </td>
              <td class="td text-xs text-neutral-600 dark:text-neutral-300">{{ new Date(u.registered_at).toLocaleDateString() }}</td>
              <td class="td text-xs text-neutral-600 dark:text-neutral-300">{{ u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—' }}</td>
              <td class="td text-right tabular-nums">{{ u.submission_count }}</td>
              <td class="td text-right tabular-nums">{{ u.campaigns_created }}</td>
              <td class="td">
                <button class="btn !py-0.5 !px-2 text-xs" :disabled="u.id === auth.user?.id"
                        @click="toggleAdmin(u)">
                  {{ u.is_admin ? '✓ admin' : 'make admin' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- =========================== Activity ============================ -->
    <div v-if="tab === 'activity'">
      <div class="flex flex-wrap gap-2 mb-3">
        <select v-model="logAction" class="input !w-48">
          <option value="">All actions</option>
          <option v-for="a in logs.actions" :key="a" :value="a">{{ a }}</option>
        </select>
        <input v-model="logUser" class="input !w-56" placeholder="Filter by username…" />
        <span class="self-center text-xs text-neutral-600 dark:text-neutral-300">
          {{ logs.total }} entries
        </span>
      </div>
      <div class="card overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-neutral-200 dark:border-neutral-800">
              <th class="th">When</th><th class="th">Who</th><th class="th">Action</th><th class="th">What</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in logs.logs" :key="l.id"
                class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
              <td class="td text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap">{{ new Date(l.created_at).toLocaleString() }}</td>
              <td class="td">{{ l.username }}</td>
              <td class="td">{{ l.action }}</td>
              <td class="td text-xs text-neutral-600 dark:text-neutral-300">{{ l.entity_type }} {{ l.details?.title || l.details?.username || l.details?.slug || l.entity_id || '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <button v-if="logs.logs.length < logs.total" class="btn mt-3" @click="loadMoreLogs">
        Load more ({{ logs.logs.length }} / {{ logs.total }})
      </button>
    </div>
  </div>
</template>
