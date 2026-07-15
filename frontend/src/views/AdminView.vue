<script setup>
import { onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'

const auth = useAuthStore()
const stats = ref(null)
const users = ref([])
const logs = ref({ total: 0, logs: [] })
const campaigns = ref([])
const error = ref('')

async function load () {
  try {
    const [s, u, l, c] = await Promise.all([
      api.adminStats(), api.adminUsers(), api.adminLogs({ limit: 50 }), api.listCampaigns()
    ])
    stats.value = s.data
    users.value = u.data
    logs.value = l.data
    campaigns.value = c.data.filter(x => x.status === 'draft')
  } catch (e) {
    error.value = errorMessage(e)
  }
}
onMounted(load)

async function toggleAdmin (u) {
  try {
    await api.setAdmin(u.id, !u.is_admin)
    await load()
  } catch (e) { error.value = errorMessage(e) }
}
async function approve (slug) {
  try { await api.approveCampaign(slug); await load() } catch (e) { error.value = errorMessage(e) }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">Administration</h1>
    <p v-if="error" class="text-red-600 dark:text-red-400 text-sm mb-3">{{ error }}</p>

    <div v-if="stats" class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
      <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.users }}</div><div class="text-xs text-neutral-500 mt-1">Users</div></div>
      <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.campaigns }}</div><div class="text-xs text-neutral-500 mt-1">Campaigns</div></div>
      <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.pending_campaigns }}</div><div class="text-xs text-neutral-500 mt-1">Pending approval</div></div>
      <div class="card p-4"><div class="text-2xl font-bold tabular-nums">{{ stats.submissions }}</div><div class="text-xs text-neutral-500 mt-1">Submissions</div></div>
    </div>

    <div v-if="campaigns.length" class="mb-6">
      <h2 class="font-semibold mb-2">Campaigns awaiting approval</h2>
      <div v-for="c in campaigns" :key="c.id" class="card p-3 mb-2 flex items-center gap-3">
        <router-link :to="`/campaigns/${c.slug}`" class="font-medium text-blue-700 dark:text-blue-400 hover:underline flex-1">
          {{ c.name }}
        </router-link>
        <span class="text-xs text-neutral-500">{{ c.start_date }} → {{ c.end_date }}</span>
        <button class="btn-primary" @click="approve(c.slug)">Approve</button>
      </div>
    </div>

    <div class="grid lg:grid-cols-2 gap-6">
      <div>
        <h2 class="font-semibold mb-2">Users</h2>
        <div class="card overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-neutral-200 dark:border-neutral-800">
                <th class="th">Username</th><th class="th">Last login</th><th class="th">Admin</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id" class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                <td class="td">{{ u.username }}</td>
                <td class="td text-xs text-neutral-500">{{ u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—' }}</td>
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
      <div>
        <h2 class="font-semibold mb-2">Audit log <span class="text-neutral-500 text-sm">({{ logs.total }})</span></h2>
        <div class="card overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-neutral-200 dark:border-neutral-800">
                <th class="th">When</th><th class="th">Who</th><th class="th">Action</th><th class="th">What</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in logs.logs" :key="l.id" class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                <td class="td text-xs text-neutral-500 whitespace-nowrap">{{ new Date(l.created_at).toLocaleString() }}</td>
                <td class="td">{{ l.username }}</td>
                <td class="td">{{ l.action }}</td>
                <td class="td text-xs text-neutral-500">{{ l.entity_type }} {{ l.details?.title || l.details?.slug || l.entity_id || '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
