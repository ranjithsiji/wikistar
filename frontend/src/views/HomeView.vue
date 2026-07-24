<script setup>
import { computed, onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'
import CampaignCard from '../components/CampaignCard.vue'

const stats = ref(null)
const campaigns = ref([])
const error = ref('')
const loading = ref(true)

// /api/campaigns is already sorted by start date, newest first.
const recent = computed(() =>
  campaigns.value.filter(c => c.status !== 'draft').slice(0, 6))

const tiles = computed(() => [
  { label: 'Total contests', value: stats.value?.campaigns },
  { label: 'Live contests', value: stats.value?.live_campaigns },
  { label: 'Participants', value: stats.value?.participants },
  { label: 'Submissions', value: stats.value?.submissions }
])

const fmt = (n) => n == null ? '—' : n.toLocaleString()

const roles = [
  {
    title: 'Participants',
    text: 'Submit articles, collaborate, and compete in global contests.',
    icon: 'users'
  },
  {
    title: 'Organizers',
    text: 'Create contests, manage tasks, and engage communities.',
    icon: 'plus'
  },
  {
    title: 'Judges',
    text: 'Review submissions and ensure fair evaluation.',
    icon: 'gavel'
  }
]

onMounted(async () => {
  try {
    const [s, c] = await Promise.all([api.siteStats(), api.listCampaigns()])
    stats.value = s.data
    campaigns.value = c.data
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-10">
    <!-- Hero: full-width, centered, decorative glows.
         Light: white with ink text; dark: deep navy with white text. -->
    <section class="full-bleed relative overflow-hidden -mt-6
                    bg-white text-neutral-900 dark:bg-[#0b1023] dark:text-white">
      <div class="pointer-events-none absolute -top-32 -right-24 h-[28rem] w-[28rem]
                  rounded-full bg-blue-500/20 dark:bg-blue-600/25 blur-3xl"></div>
      <div class="pointer-events-none absolute top-24 right-56 h-24 w-24
                  rounded-full bg-indigo-400/20 blur-2xl"></div>
      <div class="pointer-events-none absolute -bottom-28 -left-20 h-80 w-80
                  rounded-full bg-indigo-500/15 dark:bg-indigo-700/25 blur-3xl"></div>

      <div class="relative max-w-6xl mx-auto px-4 py-16 sm:py-24 text-center">
        <h1 class="text-4xl sm:text-6xl font-bold tracking-tight">
          Wiki<span class="text-blue-600 dark:text-blue-400">STAR</span>
        </h1>
        <p class="mt-6 max-w-2xl mx-auto text-lg text-neutral-500 dark:text-slate-300">
          Submit, track and review contributions for Wikipedia and Wikidata
          editathons and writing contests.
        </p>
        <div class="mt-8 flex flex-wrap justify-center gap-3">
          <router-link to="/contests"
                       class="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white
                              hover:bg-blue-500 transition-colors">
            Browse contests
          </router-link>
          <router-link to="/about"
                       class="rounded-lg px-6 py-3 text-sm font-semibold transition-colors
                              bg-neutral-100 text-neutral-900 hover:bg-neutral-200
                              dark:bg-white/10 dark:text-white dark:hover:bg-white/20">
            Learn more
          </router-link>
        </div>

        <dl class="mt-14 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto">
          <div v-for="t in tiles" :key="t.label"
               class="rounded-xl border px-4 py-3
                      border-neutral-200 bg-neutral-50 dark:border-white/10 dark:bg-white/5">
            <dd class="text-3xl font-semibold">{{ fmt(t.value) }}</dd>
            <dt class="mt-1 text-xs font-semibold uppercase tracking-wide
                       text-neutral-500 dark:text-slate-300">
              {{ t.label }}
            </dt>
          </div>
        </dl>
      </div>
    </section>

    <p v-if="error" class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>

    <!-- Recent contests -->
    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold">{{ !loading && !recent.length ? 'How it works' : 'Recent contests' }}</h2>
        <router-link to="/contests"
                     class="text-sm font-medium text-link-700 dark:text-link-400 hover:underline">
          View all contests →
        </router-link>
      </div>
      <p v-if="loading" class="text-neutral-600 dark:text-neutral-300">Loading…</p>
      <div v-else-if="recent.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <CampaignCard v-for="c in recent" :key="c.id" :campaign="c" />
      </div>

      <!-- No contests yet: introduce the roles instead -->
      <div v-else class="grid gap-4 sm:grid-cols-3">
        <div v-for="r in roles" :key="r.title" class="card p-6 text-center">
          <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full
                       bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
            <!-- users -->
            <svg v-if="r.icon === 'users'" class="w-6 h-6" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <!-- plus -->
            <svg v-else-if="r.icon === 'plus'" class="w-6 h-6" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v8m-4-4h8" />
            </svg>
            <!-- gavel -->
            <svg v-else class="w-6 h-6" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m14 13-8.5 8.5a2.12 2.12 0 1 1-3-3L11 10" />
              <path d="m16 16 6-6M8 8l6-6m1 9 5-5M9 7l5-5" />
            </svg>
          </span>
          <h3 class="mt-3 font-semibold text-lg">{{ r.title }}</h3>
          <p class="mt-1 text-sm text-neutral-600 dark:text-neutral-300">{{ r.text }}</p>
        </div>
      </div>
    </section>
  </div>
</template>
