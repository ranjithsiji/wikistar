<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'
import ClaimEditor from '../components/ClaimEditor.vue'
import LanguageSelect from '../components/LanguageSelect.vue'
import ParticipantDetails from '../components/ParticipantDetails.vue'
import ReviewForm from '../components/ReviewForm.vue'
import StatsTab from '../components/StatsTab.vue'

const props = defineProps({ slug: { type: String, required: true } })
const router = useRouter()
const auth = useAuthStore()

const campaign = ref(null)
const submissions = ref([])
const leaderboard = ref([])
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

const isOrganizer = computed(() =>
  auth.isAdmin || campaign.value?.my_roles.includes('organizer'))
const isJury = computed(() =>
  isOrganizer.value || campaign.value?.my_roles.includes('jury'))
const isParticipant = computed(() =>
  campaign.value?.my_roles.includes('participant'))
const selfMode = computed(() =>
  ['self', 'hybrid'].includes(campaign.value?.scoring_mode))
const criteria = computed(() => campaign.value?.settings?.jury_criteria || [])
const shownSubmissions = computed(() =>
  onlyMine.value
    ? submissions.value.filter(s => s.user.username === auth.user?.username)
    : submissions.value)

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

const overviewTiles = computed(() => [
  { label: 'Submissions', value: stats.value?.submissions },
  { label: 'Participants', value: stats.value?.participants },
  { label: 'Total points', value: stats.value?.total_points },
  { label: 'Reviews', value: stats.value?.reviews }
])

const tabs = computed(() => {
  const t = [['overview', 'Overview'], ['submissions', 'Submissions'],
             ['leaderboard', 'Leaderboard'], ['stats', 'Statistics']]
  return t
})

const canApprove = ref(false)
const suggestedLinks = ref(null)   // resolved Wikidata sitelinks

async function load () {
  try {
    campaign.value = (await api.getCampaign(props.slug)).data
    submissions.value = (await api.listSubmissions(props.slug)).data
    // Overview stat tiles; best-effort, never blocks the page.
    api.campaignStats(props.slug)
      .then(r => { stats.value = r.data })
      .catch(() => {})
    if (!newLanguage.value) newLanguage.value = campaign.value.language
    // Fountain model: approval needs on-wiki admin rights (jury: sysop on
    // the target wiki; self: sysop on any Wikipedia), or site admin.
    if (campaign.value.status === 'draft' && auth.isLoggedIn) {
      canApprove.value = (await api.approvalRights(props.slug)).data.can_approve
    } else {
      canApprove.value = false
    }
    // Suggested QIDs -> wikilinks in the viewer's preferred languages
    if (campaign.value.suggested_items.length && suggestedLinks.value === null) {
      try {
        suggestedLinks.value = (await api.suggestedLinks(props.slug)).data
      } catch { suggestedLinks.value = false }
    }
  } catch (e) {
    error.value = errorMessage(e)
  }
}
async function loadLeaderboard () {
  try {
    leaderboard.value = (await api.leaderboard(props.slug)).data
  } catch (e) {
    notice.value = errorMessage(e)
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
  const payload = { title: newTitle.value, kind: newKind.value }
  if (campaign.value.settings.multi_language && newKind.value === 'article') {
    payload.language = newLanguage.value || campaign.value.language
  }
  await api.createSubmission(props.slug, payload)
  newTitle.value = ''
}, 'Submission added.')
const withdraw = (s) => {
  if (!confirm(`Withdraw "${s.title}"?`)) return
  return run(() => api.deleteSubmission(s.id))
}
const refresh = (s) => run(() => api.refreshSubmission(s.id), 'Wiki metadata refreshed.')
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
  <p v-if="!campaign && error" class="text-red-600 dark:text-red-400">{{ error }}</p>
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
        <button v-if="auth.isLoggedIn && campaign.status === 'active' && !isParticipant"
                class="btn-primary" @click="join">Join campaign</button>
        <router-link v-if="isOrganizer" class="btn" :to="`/campaigns/${slug}/edit`">Edit</router-link>
        <button v-if="canApprove && campaign.status === 'draft'" class="btn-primary" @click="approve">Approve</button>
        <button v-if="canApprove && campaign.status === 'draft'" class="btn-danger" @click="reject">Reject</button>
        <button v-if="isOrganizer && campaign.status === 'active'"
                class="btn-danger" @click="deactivate">Deactivate</button>
        <button v-if="isOrganizer && (campaign.status === 'draft' || auth.isAdmin)"
                class="btn-danger" @click="remove">Delete</button>
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

    <p v-if="error" class="text-red-600 dark:text-red-400 text-sm mb-2">{{ error }}</p>
    <p v-if="notice" class="text-green-700 dark:text-green-400 text-sm mb-2">{{ notice }}</p>

    <div class="flex gap-1 border-b border-neutral-200 dark:border-neutral-800 mb-4 overflow-x-auto">
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
          <div class="flex-1 min-w-48">
            <label class="label">{{ { article: 'Article title', wikidata_item: 'Item QID', commons_file: 'File name' }[newKind] }}</label>
            <input v-model="newTitle" class="input" required
                   :placeholder="{ article: 'Article title', wikidata_item: 'Q…', commons_file: 'File:Example.jpg' }[newKind]" />
          </div>
          <div v-if="campaign.settings.multi_language && newKind === 'article'" class="w-56">
            <label class="label">Language</label>
            <LanguageSelect v-model="newLanguage" />
          </div>
          <div v-if="campaign.settings.allow_wikidata_items || campaign.settings.allow_commons_files">
            <label class="label">Type</label>
            <select v-model="newKind" class="input">
              <option value="article">Article</option>
              <option v-if="campaign.settings.allow_wikidata_items" value="wikidata_item">Wikidata item</option>
              <option v-if="campaign.settings.allow_commons_files" value="commons_file">Commons file</option>
            </select>
          </div>
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

      <div class="grid md:grid-cols-2 gap-4">
        <div class="card p-4">
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
        <div class="space-y-4">
          <div class="card p-4" v-if="campaign.suggested_articles.length || campaign.suggested_items.length">
            <h4 class="font-semibold text-sm mb-2">Suggested articles (bonus points)</h4>
            <ul class="space-y-1 text-sm list-disc pl-5">
              <li v-for="t in campaign.suggested_articles" :key="t">
                <a target="_blank"
                   :href="`https://${campaign.wiki_domain}/wiki/${t.replaceAll(' ', '_')}`"
                   class="text-blue-700 dark:text-blue-400 hover:underline">{{ t }}</a>
              </li>
            </ul>
            <template v-if="campaign.suggested_items.length">
              <div v-if="suggestedLinks && suggestedLinks.items" class="mt-3 space-y-1.5">
                <div v-for="item in suggestedLinks.items" :key="item.qid"
                     class="flex flex-wrap items-baseline gap-1.5 text-sm">
                  <a :href="`https://www.wikidata.org/wiki/${item.qid}`" target="_blank"
                     class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300 hover:underline">
                    {{ item.qid }}
                  </a>
                  <span class="font-medium">{{ item.label || '—' }}</span>
                  <a v-for="link in item.links" :key="link.lang" :href="link.url" target="_blank"
                     class="badge bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-300 hover:underline"
                     :title="link.title">{{ link.lang }}</a>
                  <span v-if="!item.links.length" class="text-xs text-neutral-500 dark:text-neutral-400">
                    no article in your languages yet — write one!
                  </span>
                </div>
                <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                  Wikilinks are shown in
                  <router-link to="/preferences" class="text-blue-600 dark:text-blue-400 hover:underline">
                    your preferred languages</router-link>
                  ({{ suggestedLinks.languages.join(', ') }}).
                </p>
              </div>
              <div v-else class="flex flex-wrap gap-1.5 mt-2">
                <a v-for="t in campaign.suggested_items" :key="t" target="_blank"
                   :href="`https://www.wikidata.org/wiki/${t}`"
                   class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300 hover:underline">{{ t }}</a>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- SUBMISSIONS -->
    <div v-if="tab === 'submissions'">
      <label v-if="auth.isLoggedIn" class="flex items-center gap-2 text-sm mb-2 cursor-pointer">
        <input type="checkbox" v-model="onlyMine" /> Show only my submissions
      </label>

      <p v-if="!shownSubmissions.length" class="text-neutral-600 dark:text-neutral-300">No submissions yet.</p>
      <div v-for="s in shownSubmissions" :key="s.id" class="card mb-2">
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
            </div>
          </div>
          <span v-if="s.status !== 'submitted'" class="badge" :class="statusStyles[s.status === 'accepted' ? 'active' : 'rejected']">
            {{ s.status }}
          </span>
          <span class="font-bold tabular-nums text-lg">{{ s.points }}<span class="text-xs font-normal text-neutral-600 dark:text-neutral-300"> pts</span></span>
        </div>

        <div v-if="expanded === s.id" class="border-t border-neutral-100 dark:border-neutral-800 p-3 space-y-4">
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
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- LEADERBOARD -->
    <div v-if="tab === 'leaderboard'">
      <p v-if="!leaderboard.length" class="text-neutral-600 dark:text-neutral-300">No points yet.</p>
      <div v-else class="card overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-neutral-200 dark:border-neutral-800">
              <th class="th">#</th><th class="th">Participant</th>
              <th class="th text-right">Submissions</th><th class="th text-right">Points</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in leaderboard" :key="row.user.id"
                class="border-b border-neutral-100 dark:border-neutral-800 last:border-0
                       cursor-pointer hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                title="Show this participant's submissions"
                @click="detailsUser = row.user">
              <td class="td tabular-nums">{{ row.rank }}</td>
              <td class="td font-medium text-blue-700 dark:text-blue-400">{{ row.user.username }}</td>
              <td class="td text-right tabular-nums">{{ row.submission_count }}</td>
              <td class="td text-right tabular-nums font-semibold">{{ row.points }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- STATISTICS -->
    <StatsTab v-if="tab === 'stats'" :slug="slug" />

    <ParticipantDetails v-if="detailsUser" :slug="slug" :user="detailsUser"
                        @close="detailsUser = null" />
  </div>
</template>
