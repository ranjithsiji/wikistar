<script setup>
import { computed, ref } from 'vue'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'

const auth = useAuthStore()

const TABS = [
  { key: 'participation', label: 'Participation', fetch: api.myParticipation },
  { key: 'submissions', label: 'Submissions', fetch: api.mySubmissions },
  { key: 'evaluation', label: 'Evaluation', fetch: api.myEvaluation },
  { key: 'created', label: 'Created', fetch: api.myCreated },
  { key: 'approval', label: 'Approval', fetch: api.myApproval },
]

const tab = ref('participation')
const data = ref({})       // key -> list, absent until loaded
const loaded = ref(false)  // all tabs fetched once, so empty ones can hide
const loading = ref(false)
const error = ref('')

const current = computed(() => data.value[tab.value])
// Tabs with content are always shown; Participation stays visible even
// when empty as the landing tab with its own "not submitted yet" message.
const visibleTabs = computed(() => TABS.filter(t =>
  t.key === 'participation' || !loaded.value || (data.value[t.key]?.length || 0) > 0))

async function load () {
  loading.value = true
  error.value = ''
  try {
    const results = await Promise.all(TABS.map(t => t.fetch()))
    data.value = Object.fromEntries(TABS.map((t, i) => [t.key, results[i].data]))
    loaded.value = true
    // Land on the first tab that actually has something, if the default
    // (Participation) is empty but the user has content elsewhere.
    if (!data.value.participation?.length) {
      const firstNonEmpty = TABS.find(t => data.value[t.key]?.length)
      if (firstNonEmpty) tab.value = firstNonEmpty.key
    }
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

load()

const withdrawing = ref(null)
async function withdraw (s) {
  if (!confirm(`Withdraw "${s.title}"?`)) return
  withdrawing.value = s.id
  try {
    await api.deleteSubmission(s.id)
    data.value = { ...data.value,
      submissions: data.value.submissions.filter(x => x.id !== s.id) }
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    withdrawing.value = null
  }
}

function relativeEnd (c) {
  const end = new Date(`${c.end_date}T23:59:59`)
  const days = Math.round((end - Date.now()) / 86400000)
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
  const abs = Math.abs(days)
  const [value, unit] = abs >= 365 ? [Math.round(days / 365), 'year']
    : abs >= 30 ? [Math.round(days / 30), 'month'] : [days, 'day']
  return days < 0 ? `ended ${rtf.format(value, unit)}` : `ends ${rtf.format(value, unit)}`
}

const STATUS_BADGE = {
  draft: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  active: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  finished: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  archived: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold tracking-tight mb-4">Dashboard</h1>

    <p v-if="auth.loaded && !auth.isLoggedIn" class="text-neutral-600 dark:text-neutral-300">
      Please <a class="text-link-700 dark:text-link-400 hover:underline"
                :href="api.loginUrl">log in</a> to see your dashboard.
    </p>

    <template v-else>
      <div class="tab-group mb-5 w-fit max-w-full overflow-x-auto">
        <button v-for="t in visibleTabs" :key="t.key" class="tab"
                :class="{ 'tab-active': tab === t.key }" @click="tab = t.key">
          {{ t.label }}
        </button>
      </div>

      <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
      <p v-else-if="loading" class="text-sm text-neutral-600 dark:text-neutral-300">Loading…</p>

      <template v-else-if="current">
        <p v-if="!current.length" class="text-sm text-neutral-600 dark:text-neutral-300">
          {{ {
            participation: 'You have not submitted to any campaign yet.',
            submissions: 'You have not submitted anything yet.',
            evaluation: 'You are not on the jury of any campaign.',
            created: 'You have not created any campaigns.',
            approval: 'No campaigns are waiting for your approval.',
          }[tab] }}
        </p>

        <!-- Participation: campaign + leaderboard window around me -->
        <div v-else-if="tab === 'participation'" class="space-y-4">
          <div v-for="c in current" :key="c.id" class="card p-4">
            <div class="flex items-baseline gap-3 flex-wrap">
              <router-link :to="`/campaigns/${c.slug}`"
                           class="font-semibold text-link-700 dark:text-link-400 hover:underline">
                {{ c.name }}
              </router-link>
              <span class="text-xs text-neutral-600 dark:text-neutral-300">{{ relativeEnd(c) }}</span>
            </div>
            <p v-if="c.hidden_marks" class="mt-2 text-sm text-neutral-600 dark:text-neutral-300">
              Marks are hidden in this campaign.
            </p>
            <template v-else>
              <!-- your own contributions in this campaign -->
              <div v-if="c.mine" class="mt-3 grid grid-cols-3 max-w-md rounded-lg
                          border border-blue-200 dark:border-blue-900
                          bg-blue-50 dark:bg-blue-950/40 divide-x divide-blue-200 dark:divide-blue-900">
                <div class="px-3 py-2 text-center">
                  <div class="text-lg font-bold tabular-nums text-blue-700 dark:text-blue-400">
                    {{ c.mine.submission_count }}
                  </div>
                  <div class="text-[11px] text-blue-900 dark:text-blue-300">Contributions</div>
                </div>
                <div class="px-3 py-2 text-center">
                  <div class="text-lg font-bold tabular-nums text-blue-700 dark:text-blue-400">
                    {{ c.mine.points }}
                  </div>
                  <div class="text-[11px] text-blue-900 dark:text-blue-300">Points</div>
                </div>
                <div class="px-3 py-2 text-center">
                  <div class="text-lg font-bold tabular-nums text-blue-700 dark:text-blue-400">
                    {{ c.mine.bytes_added.toLocaleString() }}
                  </div>
                  <div class="text-[11px] text-blue-900 dark:text-blue-300">Bytes</div>
                </div>
              </div>

              <table v-if="c.rows.length" class="mt-3 w-full max-w-md text-sm">
                <tbody>
                  <tr v-for="r in c.rows" :key="r.rank + r.username"
                      :class="r.me ? 'bg-neutral-100 dark:bg-neutral-800 font-semibold' : ''">
                    <td class="py-1 px-2 w-10 text-right tabular-nums">{{ r.rank }}</td>
                    <td class="py-1 px-2">{{ r.username }}</td>
                    <td class="py-1 px-2 text-right tabular-nums">{{ r.points.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="mt-2 text-sm text-neutral-600 dark:text-neutral-300">
                No points counted yet.
              </p>
            </template>
          </div>
        </div>

        <!-- Submissions: every submission I've made, with a withdraw action -->
        <div v-else-if="tab === 'submissions'" class="space-y-2">
          <div v-for="s in current" :key="s.id" class="card p-3 flex flex-wrap items-center gap-3">
            <div class="flex-1 min-w-40">
              <a :href="s.url" target="_blank"
                 class="font-medium text-link-700 dark:text-link-400 hover:underline">{{ s.title }}</a>
              <div class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
                <router-link :to="`/campaigns/${s.campaign.slug}`"
                             class="text-link-700 dark:text-link-400 hover:underline">
                  {{ s.campaign.name }}</router-link>
                · {{ new Date(s.submitted_at).toLocaleDateString() }}
                <template v-if="s.bytes_added"> · +{{ s.bytes_added.toLocaleString() }} bytes</template>
              </div>
            </div>
            <span v-if="s.status !== 'submitted'" class="badge" :class="STATUS_BADGE[s.status === 'accepted' ? 'active' : 'rejected']">
              {{ s.status }}
            </span>
            <span v-if="s.status !== 'rejected'" class="font-bold tabular-nums">{{ s.points }}<span class="text-xs font-normal text-neutral-600 dark:text-neutral-300"> pts</span></span>
            <button v-if="s.campaign.status === 'active'" class="btn-danger"
                    :disabled="withdrawing === s.id" @click="withdraw(s)">
              {{ withdrawing === s.id ? 'Withdrawing…' : 'Withdraw' }}
            </button>
          </div>
        </div>

        <!-- Evaluation: campaigns where I am jury, with pending count -->
        <div v-else-if="tab === 'evaluation'" class="space-y-2">
          <router-link v-for="c in current" :key="c.id" :to="`/campaigns/${c.slug}`"
                       class="card p-4 flex items-center gap-4 hover:border-neutral-300
                              dark:hover:border-neutral-700">
            <div class="flex-1 min-w-0">
              <div class="font-semibold truncate">{{ c.name }}</div>
              <div class="text-xs text-neutral-600 dark:text-neutral-300">{{ relativeEnd(c) }}</div>
            </div>
            <span class="badge tabular-nums"
                  :class="c.missing
                    ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300'
                    : 'bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400'"
                  :title="`${c.missing} submissions waiting for your review`">
              {{ c.missing }}
            </span>
          </router-link>
        </div>

        <!-- Created / Approval: plain campaign lists with status -->
        <div v-else class="space-y-2">
          <router-link v-for="c in current" :key="c.id" :to="`/campaigns/${c.slug}`"
                       class="card p-4 flex items-center gap-4 hover:border-neutral-300
                              dark:hover:border-neutral-700">
            <div class="flex-1 min-w-0">
              <div class="font-semibold truncate">{{ c.name }}</div>
              <div class="text-xs text-neutral-600 dark:text-neutral-300">{{ relativeEnd(c) }}</div>
            </div>
            <span class="badge" :class="STATUS_BADGE[c.status]">{{ c.status }}</span>
          </router-link>
        </div>
      </template>
    </template>
  </div>
</template>
