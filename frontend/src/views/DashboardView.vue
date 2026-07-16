<script setup>
import { computed, ref, watch } from 'vue'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'

const auth = useAuthStore()

const TABS = [
  { key: 'participation', label: 'Participation', fetch: api.myParticipation },
  { key: 'evaluation', label: 'Evaluation', fetch: api.myEvaluation },
  { key: 'created', label: 'Created', fetch: api.myCreated },
  { key: 'approval', label: 'Approval', fetch: api.myApproval },
]

const tab = ref('participation')
const data = ref({})       // key -> list
const loading = ref(false)
const error = ref('')

const current = computed(() => data.value[tab.value])

async function load () {
  const t = TABS.find(t => t.key === tab.value)
  if (data.value[t.key]) return
  loading.value = true
  error.value = ''
  try {
    data.value = { ...data.value, [t.key]: (await t.fetch()).data }
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

watch(tab, load, { immediate: true })

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
    <h1 class="text-2xl font-bold tracking-tight mb-4">Personal Cabinet</h1>

    <p v-if="auth.loaded && !auth.isLoggedIn" class="text-neutral-500 dark:text-neutral-400">
      Please <a class="text-blue-600 dark:text-blue-400 hover:underline"
                :href="api.loginUrl">log in</a> to see your dashboard.
    </p>

    <template v-else>
      <div class="flex gap-1 border-b border-neutral-200 dark:border-neutral-800 mb-5 overflow-x-auto">
        <button v-for="t in TABS" :key="t.key" class="tab"
                :class="{ 'tab-active': tab === t.key }" @click="tab = t.key">
          {{ t.label }}
        </button>
      </div>

      <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
      <p v-else-if="loading" class="text-sm text-neutral-500 dark:text-neutral-400">Loading…</p>

      <template v-else-if="current">
        <p v-if="!current.length" class="text-sm text-neutral-500 dark:text-neutral-400">
          {{ {
            participation: 'You have not submitted to any campaign yet.',
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
                           class="font-semibold text-blue-700 dark:text-blue-400 hover:underline">
                {{ c.name }}
              </router-link>
              <span class="text-xs text-neutral-500 dark:text-neutral-400">{{ relativeEnd(c) }}</span>
            </div>
            <p v-if="c.hidden_marks" class="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
              Marks are hidden in this campaign.
            </p>
            <table v-else-if="c.rows.length" class="mt-3 w-full max-w-md text-sm">
              <tbody>
                <tr v-for="r in c.rows" :key="r.rank + r.username"
                    :class="r.me ? 'bg-neutral-100 dark:bg-neutral-800 font-semibold' : ''">
                  <td class="py-1 px-2 w-10 text-right tabular-nums">{{ r.rank }}</td>
                  <td class="py-1 px-2">{{ r.username }}</td>
                  <td class="py-1 px-2 text-right tabular-nums">{{ r.points.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
              No points counted yet.
            </p>
          </div>
        </div>

        <!-- Evaluation: campaigns where I am jury, with pending count -->
        <div v-else-if="tab === 'evaluation'" class="space-y-2">
          <router-link v-for="c in current" :key="c.id" :to="`/campaigns/${c.slug}`"
                       class="card p-4 flex items-center gap-4 hover:border-neutral-300
                              dark:hover:border-neutral-700">
            <div class="flex-1 min-w-0">
              <div class="font-semibold truncate">{{ c.name }}</div>
              <div class="text-xs text-neutral-500 dark:text-neutral-400">{{ relativeEnd(c) }}</div>
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
              <div class="text-xs text-neutral-500 dark:text-neutral-400">{{ relativeEnd(c) }}</div>
            </div>
            <span class="badge" :class="STATUS_BADGE[c.status]">{{ c.status }}</span>
          </router-link>
        </div>
      </template>
    </template>
  </div>
</template>
