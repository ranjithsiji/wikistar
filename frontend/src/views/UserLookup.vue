<template>
  <div class="user-lookup-page bg-light min-vh-100">

    <!-- Page Header -->
    <div class="page-header bg-white border-bottom shadow-sm">
      <div class="container-xl">
        <div class="d-flex align-items-center gap-3 py-3">
          <div class="avatar-icon">🔍</div>
          <div>
            <h1 class="page-title mb-0">Wiki User Lookup</h1>
            <p class="text-muted small mb-0">Check user rights and contributions on any Wikimedia project</p>
          </div>
        </div>
      </div>
    </div>

    <div class="container-xl py-4">

      <!-- Access denied -->
      <div v-if="!isPrivileged" class="alert alert-danger text-center py-5">
        <div style="font-size:3rem;">🚫</div>
        <h4>Access Restricted</h4>
        <p>This tool is available to Admin, Coordinator, and Jury roles only.</p>
        <button class="btn btn-primary" @click="$router.push('/')">Return Home</button>
      </div>

      <div v-else>
        <!-- Search Form -->
        <div class="card shadow-sm border-0 rounded-3 mb-4">
          <div class="card-body p-4">
            <h5 class="fw-bold mb-3">Search a User</h5>
            <div class="row g-3 align-items-end">
              <div class="col-md-4">
                <label class="form-label fw-semibold small text-uppercase">Wiki Username</label>
                <input
                  v-model="searchUsername"
                  type="text"
                  class="form-control"
                  placeholder="e.g. Ranjithsiji"
                  @keyup.enter="lookup"
                />
              </div>
              <div class="col-md-4">
                <label class="form-label fw-semibold small text-uppercase">Project Domain</label>
                <div class="input-group">
                  <input
                    v-model="searchWiki"
                    type="text"
                    class="form-control"
                    placeholder="e.g. ml.wikipedia.org"
                  />
                </div>
                <div class="mt-1 d-flex flex-wrap gap-1">
                  <button v-for="preset in wikiPresets" :key="preset" class="btn btn-xs btn-outline-secondary"
                    @click="searchWiki = preset">{{ preset }}</button>
                </div>
              </div>
              <div class="col-md-2">
                <label class="form-label fw-semibold small text-uppercase">Contribs Limit</label>
                <select v-model="contribsLimit" class="form-select">
                  <option :value="10">10</option>
                  <option :value="20">20</option>
                  <option :value="50">50</option>
                </select>
              </div>
              <div class="col-md-2">
                <button class="btn btn-primary w-100" @click="lookup" :disabled="loading">
                  <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                  {{ loading ? 'Looking up...' : '🔍 Lookup' }}
                </button>
              </div>
            </div>
            <div v-if="errorMsg" class="alert alert-danger mt-3 mb-0 py-2">{{ errorMsg }}</div>
          </div>
        </div>

        <!-- Results -->
        <div v-if="result" class="row g-4">

          <!-- Left: User Profile Card -->
          <div class="col-lg-4">
            <div class="card shadow-sm border-0 rounded-3 h-100">
              <div class="card-body p-4">
                <div class="d-flex align-items-center gap-3 mb-4">
                  <div class="user-avatar" :class="result.user.is_sysop ? 'sysop' : ''">
                    {{ result.user.username?.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <h5 class="mb-0 fw-bold">{{ result.user.username }}</h5>
                    <a :href="result.user.wiki_profile_url" target="_blank" class="text-muted small text-decoration-none">
                      {{ result.wiki_domain }} ↗
                    </a>
                  </div>
                </div>

                <!-- Key Stats -->
                <div class="row g-2 mb-3">
                  <div class="col-6">
                    <div class="stat-box text-center border rounded p-2">
                      <div class="stat-value text-primary">{{ result.user.editcount?.toLocaleString() }}</div>
                      <div class="stat-label">Total Edits</div>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="stat-box text-center border rounded p-2">
                      <div class="stat-value" :class="result.user.is_sysop ? 'text-success' : 'text-muted'">
                        {{ result.user.is_sysop ? '✓ Yes' : 'No' }}
                      </div>
                      <div class="stat-label">Sysop</div>
                    </div>
                  </div>
                </div>

                <!-- Registration Date -->
                <div class="info-row mb-3">
                  <span class="info-label">Member Since</span>
                  <span class="info-val">{{ formatDate(result.user.registration) }}</span>
                </div>

                <!-- Blocked Status -->
                <div v-if="result.user.blocked" class="alert alert-danger py-2 small mb-3">
                  ⛔ <strong>User is blocked</strong><br>
                  <span class="text-muted">{{ result.user.block_reason }}</span>
                </div>

                <!-- Groups -->
                <div class="mb-3">
                  <div class="info-label mb-1">Wiki Groups</div>
                  <div class="d-flex flex-wrap gap-1">
                    <span v-for="g in result.user.groups" :key="g"
                      class="badge"
                      :class="groupBadgeClass(g)">{{ g }}</span>
                  </div>
                </div>

                <!-- Rights -->
                <details class="mt-3">
                  <summary class="info-label cursor-pointer">All Rights ({{ result.user.rights?.length || 0 }})</summary>
                  <div class="mt-2 d-flex flex-wrap gap-1" style="max-height: 160px; overflow-y: auto;">
                    <span v-for="r in result.user.rights" :key="r" class="badge bg-light text-dark border small">{{ r }}</span>
                  </div>
                </details>
              </div>
            </div>
          </div>

          <!-- Right: Contributions -->
          <div class="col-lg-8">
            <div class="card shadow-sm border-0 rounded-3">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h5 class="fw-bold mb-0">Recent Contributions <span class="text-muted small fw-normal">(mainspace, latest {{ result.contributions_count }})</span></h5>
                  <a :href="`https://${result.wiki_domain}/wiki/Special:Contributions/${result.user.username}`" target="_blank" class="btn btn-sm btn-outline-secondary">
                    View All ↗
                  </a>
                </div>

                <div v-if="result.contributions.length === 0" class="text-muted text-center py-4">
                  No recent mainspace contributions found.
                </div>

                <div v-else class="contribs-list">
                  <div v-for="c in result.contributions" :key="c.revid" class="contrib-row">
                    <div class="d-flex align-items-start gap-2">
                      <div class="contrib-badges flex-shrink-0 mt-1">
                        <span v-if="c.new" class="badge bg-success" title="New article">N</span>
                        <span v-if="c.minor" class="badge bg-secondary" title="Minor edit">m</span>
                      </div>
                      <div class="contrib-main flex-grow-1 min-width-0">
                        <div class="d-flex justify-content-between align-items-start gap-2">
                          <a :href="c.article_url" target="_blank" class="contrib-title fw-semibold text-decoration-none text-truncate">
                            {{ c.title }}
                          </a>
                          <span class="size-diff flex-shrink-0"
                            :class="c.sizediff > 0 ? 'text-success' : c.sizediff < 0 ? 'text-danger' : 'text-muted'">
                            {{ c.sizediff > 0 ? '+' : '' }}{{ c.sizediff?.toLocaleString() }}
                          </span>
                        </div>
                        <div class="d-flex justify-content-between gap-2 mt-1">
                          <span class="contrib-comment text-muted small text-truncate" :title="c.comment">
                            {{ c.comment || '(no summary)' }}
                          </span>
                          <span class="contrib-time text-muted small flex-shrink-0">{{ formatTime(c.timestamp) }}</span>
                        </div>
                      </div>
                      <a :href="c.diff_url" target="_blank" class="btn btn-xs btn-outline-secondary flex-shrink-0" title="View diff">diff</a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else-if="!loading && !errorMsg" class="text-center text-muted py-5">
          <div style="font-size: 3rem; opacity: 0.3;">👤</div>
          <p class="mt-2">Enter a username and project domain to look up their wiki profile.</p>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { store } from '../store'

const searchUsername = ref('')
const searchWiki = ref('en.wikipedia.org')
const contribsLimit = ref(20)
const loading = ref(false)
const errorMsg = ref('')
const result = ref(null)

const wikiPresets = [
  'en.wikipedia.org',
  'ml.wikipedia.org',
  'hi.wikipedia.org',
  'ta.wikipedia.org',
  'te.wikipedia.org',
  'bn.wikipedia.org',
  'commons.wikimedia.org',
]

const isPrivileged = computed(() => {
  return store.user && ['admin', 'coordinator', 'jury'].includes(store.user.role)
})

async function lookup() {
  if (!searchUsername.value.trim()) {
    errorMsg.value = 'Please enter a username.'
    return
  }
  loading.value = true
  errorMsg.value = ''
  result.value = null
  try {
    const res = await axios.get('/api/wiki/user-info', {
      params: {
        username: searchUsername.value.trim(),
        wiki: searchWiki.value.trim(),
        limit: contribsLimit.value
      }
    })
    result.value = res.data
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to fetch user info.'
  } finally {
    loading.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
}

function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function groupBadgeClass(group) {
  const map = {
    sysop: 'bg-danger text-white',
    bureaucrat: 'bg-dark text-white',
    bot: 'bg-secondary text-white',
    autoconfirmed: 'bg-success text-white',
    confirmed: 'bg-success text-white',
    '*': 'bg-light text-dark border',
    user: 'bg-primary text-white',
    checkuser: 'bg-warning text-dark',
    steward: 'bg-purple text-white',
    oversighter: 'bg-danger text-white',
  }
  return map[group] || 'bg-light text-dark border'
}
</script>

<style scoped>
.page-header { border-bottom: 1px solid #e9ecef; }
.page-title { font-size: 1.3rem; font-weight: 700; color: #1a1a2e; }

.avatar-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem;
}

.user-avatar {
  width: 54px; height: 54px; border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #3b82f6);
  color: white; font-size: 1.5rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.user-avatar.sysop {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
}

.stat-box { border-radius: 8px; }
.stat-value { font-size: 1.3rem; font-weight: 700; }
.stat-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; }

.info-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; font-weight: 600; }
.info-val { font-size: 0.9rem; font-weight: 500; }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid #f3f4f6; }

/* Contributions list */
.contribs-list {
  display: flex; flex-direction: column; gap: 0;
  max-height: 520px; overflow-y: auto;
}

.contrib-row {
  padding: 0.65rem 0;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.1s;
}
.contrib-row:hover { background: #f8fafc; }

.contrib-title { font-size: 0.9rem; color: #1d4ed8; max-width: 360px; display: block; }
.contrib-comment { font-size: 0.8rem; max-width: 300px; display: block; }
.contrib-time { font-size: 0.78rem; }

.size-diff { font-size: 0.82rem; font-weight: 600; }

.btn-xs {
  padding: 0.2rem 0.45rem;
  font-size: 0.75rem;
  border-radius: 4px;
  line-height: 1.3;
}

details summary { cursor: pointer; }
details summary:hover { color: #2563eb; }

.cursor-pointer { cursor: pointer; }

.min-width-0 { min-width: 0; }

@media (max-width: 767px) {
  .contrib-title { max-width: 180px; }
}
</style>
