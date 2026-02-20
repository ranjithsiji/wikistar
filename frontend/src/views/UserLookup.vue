<template>
  <div class="lookup-page">

    <!-- ── Search Form (Vertical) ── -->
    <div class="search-card">
      <h2 class="search-title">Lookup User Contributions</h2>
      <div class="form-group relative">
        <label>Project</label>
        <input 
          v-model="project" 
          @input="onProjectInput"
          placeholder="e.g. ml.wikipedia.org" 
          class="v-input"
          @focus="onProjectInput"
          @blur="closeProjectSuggestions"
        />
        <ul v-if="projectSuggestions.length" class="autocomplete-dropdown">
          <li v-for="p in projectSuggestions" :key="p" @mousedown.prevent="selectProject(p)">
            {{ p }}
          </li>
        </ul>
      </div>

      <div class="form-group relative">
        <label>Wiki Username</label>
        <input 
          v-model="username" 
          @input="onUserSearch"
          placeholder="e.g. Ranjithsiji" 
          class="v-input"
          @keyup.enter="lookup"
          @blur="closeUserSuggestions"
        />
        <ul v-if="userSuggestions.length" class="autocomplete-dropdown">
          <li v-for="u in userSuggestions" :key="u" @mousedown.prevent="selectUser(u)">
            {{ u }}
          </li>
        </ul>
      </div>

      <button class="v-lookup-btn" @click="lookup" :disabled="loading">
        <span v-if="loading" class="spinner"></span>
        <span v-else>🔍 Lookup</span>
      </button>
    </div>

    <!-- ── Error ── -->
    <div v-if="error" class="error-banner">{{ error }}</div>

    <!-- ── Access denied ── -->
    <div v-if="!isPrivileged && !loading" class="access-denied">
      <p>🚫 This tool is available to Admin, Coordinator, and Jury roles only.</p>
    </div>

    <!-- ── Results ── -->
    <div v-if="result" class="results-grid">

      <!-- Left: Profile Card -->
      <div class="card profile-card">
        <div class="avatar" :class="{ sysop: result.isSysop }">
          {{ result.username?.charAt(0)?.toUpperCase() }}
        </div>
        <div class="profile-name">{{ result.username }}</div>
        <div class="profile-project">
          <a :href="`https://${result.project}/wiki/User:${encodeURIComponent(result.username)}`" target="_blank">
            {{ result.project }} ↗
          </a>
        </div>

        <!-- Groups -->
        <div class="groups">
          <span v-for="g in result.groups" :key="g" class="group-badge" :class="groupClass(g)">{{ g }}</span>
        </div>

        <div class="profile-stats">
          <div class="pstat">
            <span class="pstat-val">{{ fmt(result.liveEdits) }}</span>
            <span class="pstat-lbl">Live edits</span>
          </div>
          <div class="pstat">
            <span class="pstat-val">{{ fmt(result.deletedEdits) }}</span>
            <span class="pstat-lbl">Deleted edits</span>
          </div>
          <div class="pstat">
            <span class="pstat-val">{{ fmt(result.creations) }}</span>
            <span class="pstat-lbl">New pages</span>
          </div>
        </div>

        <a :href="`https://xtools.wmcloud.org/ec/${result.project}/${encodeURIComponent(result.username)}`"
           target="_blank" class="xtools-link">Full XTools Report ↗</a>
      </div>

      <!-- Right: Detailed Stats -->
      <div class="right-col">

        <!-- Namespace Breakdown -->
        <div class="card">
          <h3>Edits by Namespace</h3>
          <div class="ns-list">
            <div v-for="ns in result.namespaceSorted" :key="ns.id" class="ns-row">
              <span class="ns-name">{{ ns.name }}</span>
              <div class="ns-bar-wrap">
                <div class="ns-bar" :style="{ width: ns.pct + '%', background: ns.color }"></div>
              </div>
              <span class="ns-count">{{ fmt(ns.count) }}</span>
            </div>
          </div>
        </div>

        <!-- Log Actions Summary -->
        <div class="card" v-if="result.topLogs?.length">
          <h3>Admin Actions (Log Summary)</h3>
          <div class="log-grid">
            <div v-for="log in result.topLogs" :key="log.key" class="log-item">
              <span class="log-icon">{{ log.icon }}</span>
              <span class="log-label">{{ log.label }}</span>
              <span class="log-count">{{ fmt(log.count) }}</span>
            </div>
          </div>
        </div>

        <!-- Recent Contributions -->
        <div class="card" v-if="result.contributions?.length">
          <div class="card-header-row">
            <h3>Recent Contributions</h3>
            <a :href="`https://${result.project}/wiki/Special:Contributions/${encodeURIComponent(result.username)}`"
               target="_blank" class="view-all">View All ↗</a>
          </div>
          <div class="contrib-list">
            <div v-for="c in result.contributions" :key="c.revid" class="contrib-row">
              <div class="contrib-badges">
                <span v-if="c.new" class="badge-n" title="New">N</span>
                <span v-if="c.minor" class="badge-m" title="Minor">m</span>
              </div>
              <div class="contrib-body">
                <a :href="c.article_url" target="_blank" class="contrib-title">{{ c.title }}</a>
                <span class="contrib-comment">{{ c.comment || '(no summary)' }}</span>
              </div>
              <div class="contrib-right">
                <span class="size-diff" :class="c.sizediff > 0 ? 'pos' : c.sizediff < 0 ? 'neg' : 'neu'">
                  {{ c.sizediff > 0 ? '+' : '' }}{{ c.sizediff?.toLocaleString() }}
                </span>
                <span class="contrib-time">{{ fmtTime(c.timestamp) }}</span>
                <a :href="c.diff_url" target="_blank" class="diff-btn">diff</a>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading && !error && isPrivileged" class="empty-state">
      <div class="empty-icon">👤</div>
      <p>Enter a username and project to look up their wiki profile and contributions.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { store } from '../store'

const username = ref('')
const project = ref('en.wikipedia.org')
const loading = ref(false)
const error = ref('')
const result = ref(null)

// Autocomplete state
const projectSuggestions = ref([])
const userSuggestions = ref([])
let searchTimeout = null

const ALL_PROJECTS = [
  'en.wikipedia.org', 'ml.wikipedia.org', 'hi.wikipedia.org',
  'ta.wikipedia.org', 'te.wikipedia.org', 'bn.wikipedia.org',
  'commons.wikimedia.org', 'wikidata.org', 'meta.wikimedia.org',
  'fr.wikipedia.org', 'de.wikipedia.org', 'es.wikipedia.org', 'ru.wikipedia.org'
]

function onProjectInput() {
  const q = project.value.toLowerCase().trim()
  if (!q) {
    projectSuggestions.value = ALL_PROJECTS.slice(0, 5)
    return
  }
  projectSuggestions.value = ALL_PROJECTS.filter(p => p.includes(q) && p !== q)
}

function selectProject(p) {
  project.value = p
  projectSuggestions.value = []
}

function closeProjectSuggestions() {
  projectSuggestions.value = []
}

function onUserSearch() {
  const q = username.value.trim()
  userSuggestions.value = []
  if (!q || q.length < 2) return

  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    try {
      const proj = project.value.trim() || 'en.wikipedia.org'
      const url = `https://${proj}/w/api.php?action=query&list=allusers&auprefix=${encodeURIComponent(q)}&format=json&origin=*`
      const res = await axios.get(url)
      const users = res.data?.query?.allusers || []
      userSuggestions.value = users.map(u => u.name)
    } catch(e) {
      console.error('User autocomplete failed:', e)
    }
  }, 300)
}

function selectUser(u) {
  username.value = u
  userSuggestions.value = []
}

function closeUserSuggestions() {
  userSuggestions.value = []
}

const isPrivileged = computed(() =>
  store.user && ['admin', 'coordinator', 'jury'].includes(store.user.role)
)

// Namespace ID → human name map
const NS_NAMES = {
  '0': 'Article', '1': 'Talk', '2': 'User', '3': 'User Talk',
  '4': 'Project', '5': 'Project Talk', '6': 'File', '7': 'File Talk',
  '8': 'MediaWiki', '9': 'MediaWiki Talk', '10': 'Template',
  '11': 'Template Talk', '12': 'Help', '13': 'Help Talk',
  '14': 'Category', '15': 'Category Talk', '100': 'Portal',
  '118': 'Draft', '119': 'Draft Talk', '828': 'Module', '829': 'Module Talk'
}

const NS_COLORS = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ec4899',
                   '#06b6d4','#84cc16','#f97316','#6366f1','#14b8a6']

const LOG_MAP = {
  'delete-delete':   { icon: '🗑️', label: 'Deletions' },
  'delete-restore':  { icon: '♻️', label: 'Restorations' },
  'block-block':     { icon: '⛔', label: 'Blocks' },
  'block-unblock':   { icon: '✅', label: 'Unblocks' },
  'move-move':       { icon: '📦', label: 'Page moves' },
  'protect-protect': { icon: '🔒', label: 'Protections' },
  'patrol-patrol':   { icon: '👁️', label: 'Patrols' },
  'import-interwiki':{ icon: '📥', label: 'Imports' },
  'rights-rights':   { icon: '🔑', label: 'Rights changes' },
  'thanks-thank':    { icon: '🙏', label: 'Thanks' },
  'create-create':   { icon: '📄', label: 'Account creations' },
}

async function lookup() {
  if (!username.value.trim()) { error.value = 'Enter a username.'; return }
  if (!isPrivileged.value) { error.value = 'Access denied.'; return }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const proj = project.value.trim().replace(/^https?:\/\//, '').replace(/\/$/, '')
    const user = username.value.trim()

    // 1. XTools simple_editcount
    const [simpleRes, nsRes, logRes, contribRes] = await Promise.all([
      axios.get(`https://xtools.wmcloud.org/api/user/simple_editcount/${proj}/${encodeURIComponent(user)}`),
      axios.get(`https://xtools.wmcloud.org/api/user/namespace_totals/${proj}/${encodeURIComponent(user)}`),
      axios.get(`https://xtools.wmcloud.org/api/user/log_counts/${proj}/${encodeURIComponent(user)}`),
      axios.get(`/api/wiki/user-info`, { params: { username: user, wiki: proj, limit: 20 } })
    ])

    const s = simpleRes.data
    const ns = nsRes.data?.namespace_totals || {}
    const logs = logRes.data?.log_counts || {}

    const totalNs = Object.values(ns).reduce((a, b) => a + b, 0)
    const namespaceSorted = Object.entries(ns)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([id, count], i) => ({
        id,
        name: NS_NAMES[id] || `NS ${id}`,
        count,
        pct: totalNs ? Math.round((count / totalNs) * 100) : 0,
        color: NS_COLORS[i % NS_COLORS.length]
      }))

    const topLogs = Object.entries(logs)
      .filter(([key, val]) => val > 0 && LOG_MAP[key])
      .sort((a, b) => b[1] - a[1])
      .slice(0, 9)
      .map(([key, count]) => ({ key, count, ...LOG_MAP[key] }))

    result.value = {
      username: s.username || user,
      project: proj,
      liveEdits: s.live_edit_count || 0,
      deletedEdits: s.deleted_edit_count || 0,
      creations: s.creation_count || 0,
      groups: s.user_groups || [],
      isSysop: (s.user_groups || []).includes('sysop'),
      namespaceSorted,
      topLogs,
      contributions: contribRes.data?.contributions || []
    }
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = `User "${username.value}" not found on ${project.value}.`
    } else {
      error.value = err.response?.data?.error || err.message || 'Failed to fetch user info.'
    }
  } finally {
    loading.value = false
  }
}

function fmt(n) { return (n || 0).toLocaleString() }

function fmtTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' })
}

function groupClass(g) {
  const m = { sysop: 'g-sysop', bureaucrat: 'g-bureaucrat', bot: 'g-bot',
              checkuser: 'g-check', steward: 'g-steward', 'interface-admin': 'g-ia',
              autoconfirmed: 'g-auto', confirmed: 'g-auto', user: 'g-user', '*': 'g-star' }
  return m[g] || 'g-other'
}
</script>

<style scoped>
/* ── Page ── */
.lookup-page {
  min-height: 100vh;
  background: #f8f9fa;
  font-family: 'Inter', system-ui, sans-serif;
  padding-bottom: 60px;
}

/* ── Search Form (Vertical) ── */
.search-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 30px;
  max-width: 500px;
  margin: 40px auto;
  box-shadow: 0 4px 6px rgba(0,0,0,.04);
}

.search-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin-top: 0;
  margin-bottom: 24px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 0.82rem;
  font-weight: 700;
  color: #374151;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.v-input {
  width: 100%;
  padding: 12px 14px;
  font-size: 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  color: #111827;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.v-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

/* Autocomplete drops */
.relative { position: relative; }
.autocomplete-dropdown {
  position: absolute;
  top: 100%; left: 0; right: 0;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  margin: 4px 0 0; padding: 0;
  list-style: none;
  max-height: 200px;
  overflow-y: auto;
  z-index: 50;
  box-shadow: 0 4px 12px rgba(0,0,0,.15);
}
.autocomplete-dropdown li {
  padding: 10px 14px;
  font-size: 0.95rem;
  color: #374151;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
}
.autocomplete-dropdown li:last-child { border-bottom: none; }
.autocomplete-dropdown li:hover { background: #f3f4f6; color: #111827; }

/* Vert Lookup btn */
.v-lookup-btn {
  width: 100%;
  padding: 14px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background .15s;
  margin-top: 10px;
}
.v-lookup-btn:hover:not(:disabled) { background: #1d4ed8; }
.v-lookup-btn:disabled { background: #93c5fd; cursor: default; }

.spinner {
  width: 18px; height: 18px;
  border: 3px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg) } }

/* ── Error / Access denied ── */
.error-banner {
  max-width: 500px;
  margin: -20px auto 20px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: .9rem;
  text-align: center;
}
.access-denied {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

/* ── Results layout ── */
.results-grid {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
  padding: 24px 32px;
  align-items: start;
}

/* ── Card ── */
.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}
.card:last-child { margin-bottom: 0; }

.card h3 {
  font-size: .9rem;
  font-weight: 700;
  color: #374151;
  margin: 0 0 14px;
  text-transform: uppercase;
  letter-spacing: .5px;
}

/* ── Profile card ── */
.profile-card {
  text-align: center;
  position: sticky;
  top: 20px;
}

.avatar {
  width: 64px; height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #3b82f6);
  color: #fff;
  font-size: 1.8rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 12px;
}
.avatar.sysop { background: linear-gradient(135deg, #dc2626, #b91c1c); }

.profile-name {
  font-size: 1.1rem; font-weight: 700; color: #111827; margin-bottom: 4px;
}
.profile-project a {
  font-size: .8rem; color: #6b7280; text-decoration: none;
}
.profile-project a:hover { text-decoration: underline; }

.groups {
  display: flex; flex-wrap: wrap; gap: 4px;
  justify-content: center; margin: 12px 0;
}
.group-badge {
  padding: 2px 8px; border-radius: 12px; font-size: .72rem; font-weight: 600;
}
.g-sysop     { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.g-bureaucrat{ background: #1f2937; color: #fff; }
.g-bot       { background: #f3f4f6; color: #6b7280; border: 1px solid #d1d5db; }
.g-check     { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
.g-steward   { background: #ede9fe; color: #5b21b6; }
.g-ia        { background: #ecfdf5; color: #065f46; }
.g-auto      { background: #eff6ff; color: #1d4ed8; }
.g-user      { background: #f3f4f6; color: #374151; }
.g-star, .g-other { display: none; }

.profile-stats {
  display: flex; justify-content: space-between;
  border-top: 1px solid #f3f4f6; padding-top: 12px; margin-top: 12px;
  text-align: center;
}
.pstat-val {
  display: block; font-size: 1.15rem; font-weight: 700; color: #1d4ed8;
}
.pstat-lbl {
  display: block; font-size: .68rem; color: #9ca3af; margin-top: 2px;
}

.xtools-link {
  display: inline-block; margin-top: 14px;
  font-size: .78rem; color: #6b7280; text-decoration: none;
  border: 1px solid #e5e7eb; border-radius: 6px; padding: 4px 10px;
}
.xtools-link:hover { background: #f9fafb; }

/* ── Namespace bars ── */
.ns-list { display: flex; flex-direction: column; gap: 8px; }
.ns-row { display: flex; align-items: center; gap: 8px; }
.ns-name { width: 110px; font-size: .8rem; color: #374151; flex-shrink: 0; }
.ns-bar-wrap {
  flex: 1; height: 8px; background: #f3f4f6; border-radius: 4px; overflow: hidden;
}
.ns-bar { height: 100%; border-radius: 4px; transition: width .5s; }
.ns-count { font-size: .8rem; font-weight: 600; color: #374151; width: 50px; text-align: right; }

/* ── Log grid ── */
.log-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
}
.log-item {
  display: flex; flex-direction: column; align-items: center;
  background: #f9fafb; border-radius: 8px; padding: 10px 8px; text-align: center;
}
.log-icon { font-size: 1.2rem; margin-bottom: 4px; }
.log-label { font-size: .72rem; color: #6b7280; }
.log-count { font-size: 1rem; font-weight: 700; color: #111827; margin-top: 2px; }

/* ── Contributions ── */
.card-header-row {
  display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px;
}
.card-header-row h3 { margin: 0; }
.view-all { font-size: .8rem; color: #6b7280; text-decoration: none; }
.view-all:hover { text-decoration: underline; }

.contrib-list { display: flex; flex-direction: column; }
.contrib-row {
  display: flex; align-items: flex-start; gap: 6px;
  padding: 7px 0; border-bottom: 1px solid #f3f4f6;
}
.contrib-row:last-child { border-bottom: none; }

.contrib-badges { display: flex; flex-direction: column; gap: 2px; flex-shrink: 0; width: 16px; margin-top: 2px; }
.badge-n, .badge-m {
  font-size: .65rem; font-weight: 700; width: 14px; height: 14px;
  display: flex; align-items: center; justify-content: center; border-radius: 3px;
}
.badge-n { background: #d1fae5; color: #065f46; }
.badge-m { background: #f3f4f6; color: #6b7280; }

.contrib-body { flex: 1; min-width: 0; }
.contrib-title {
  display: block; font-size: .88rem; font-weight: 600;
  color: #1d4ed8; text-decoration: none; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}
.contrib-title:hover { text-decoration: underline; }
.contrib-comment {
  display: block; font-size: .75rem; color: #6b7280;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;
}

.contrib-right {
  display: flex; flex-direction: column; align-items: flex-end; gap: 2px; flex-shrink: 0;
}
.size-diff { font-size: .8rem; font-weight: 600; }
.pos { color: #059669; }
.neg { color: #dc2626; }
.neu { color: #9ca3af; }
.contrib-time { font-size: .72rem; color: #9ca3af; }
.diff-btn {
  font-size: .7rem; border: 1px solid #d1d5db; border-radius: 4px;
  padding: 1px 6px; color: #6b7280; text-decoration: none;
}
.diff-btn:hover { background: #f3f4f6; }

/* ── Empty state ── */
.empty-state {
  text-align: center; padding: 60px 20px; color: #9ca3af;
}
.empty-icon { font-size: 3rem; opacity: .3; margin-bottom: 12px; }

/* ── Right col ── */
.right-col { min-width: 0; }

@media (max-width: 768px) {
  .results-grid { grid-template-columns: 1fr; }
}
</style>
