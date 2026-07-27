<script setup>
import { computed, onMounted, ref, watch } from 'vue'
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
  if (panel.value === 'articles') await loadArticles()
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
          <div class="overflow-x-auto mb-3">
            <table class="w-full">
              <thead>
                <tr class="border-b border-neutral-200 dark:border-neutral-800">
                  <th class="th">User</th><th class="th">Role</th><th class="th text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!campaign.members.length">
                  <td class="td text-sm text-neutral-600 dark:text-neutral-300" colspan="3">
                    No members yet.
                  </td>
                </tr>
                <tr v-for="m in campaign.members" :key="m.id"
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
                       class="text-link-700 dark:text-link-400 hover:underline">{{ s.title }}</a>
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
    </template>
  </div>
</template>
