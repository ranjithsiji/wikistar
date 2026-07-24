<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'
import ReviewForm from '../components/ReviewForm.vue'

// Fountain-style judging mode: article list with per-juror indicators on
// the left, the rendered article on the right, review controls below.
const props = defineProps({ slug: { type: String, required: true } })
const auth = useAuthStore()

const campaign = ref(null)
const submissions = ref([])
const selected = ref(null)
const articleHtml = ref('')
const articleWords = ref(0)
const articleLoading = ref(false)
const error = ref('')
const notice = ref('')

const isJury = computed(() =>
  auth.isAdmin || ['jury', 'organizer'].some(r => campaign.value?.my_roles.includes(r)))
const criteria = computed(() => campaign.value?.settings?.jury_criteria || [])
const juryNames = computed(() =>
  campaign.value?.members.filter(m => m.role === 'jury').map(m => m.user.username) || [])

// Everything reviewable by me: everyone else's submissions.
const queue = computed(() =>
  submissions.value.filter(s => s.user.username !== auth.user?.username))
const myReview = (s) => s.reviews.find(r => r.reviewer.username === auth.user?.username)
const reviewedByMe = computed(() => queue.value.filter(s => myReview(s)).length)
const remaining = computed(() => queue.value.length - reviewedByMe.value)

const decisionStyles = {
  accept: 'bg-green-500 border-green-500',
  reject: 'bg-red-500 border-red-500',
  needs_work: 'bg-amber-500 border-amber-500'
}
function juryDecision (s, name) {
  return s.reviews.find(r => r.reviewer.username === name)?.decision
}

async function load (keepSelection = false) {
  try {
    campaign.value = (await api.getCampaign(props.slug)).data
    submissions.value = (await api.listSubmissions(props.slug)).data
    if (keepSelection && selected.value) {
      selected.value = queue.value.find(s => s.id === selected.value.id) || selected.value
    } else {
      selected.value = queue.value.find(s => !myReview(s)) || queue.value[0] || null
    }
  } catch (e) {
    error.value = errorMessage(e)
  }
}
onMounted(load)

// ---- article pane ----------------------------------------------------------
watch(selected, async (s) => {
  articleHtml.value = ''
  articleWords.value = 0
  if (!s) return
  articleLoading.value = true
  try {
    const url = `https://${s.wiki_domain}/w/api.php?action=parse`
      + `&page=${encodeURIComponent(s.title)}&prop=text&formatversion=2`
      + `&redirects=1&disableeditsection=1&format=json&origin=*`
    const data = await (await fetch(url)).json()
    articleHtml.value = data.parse?.text || ''
    const holder = document.createElement('div')
    holder.innerHTML = articleHtml.value
    articleWords.value = (holder.textContent || '').trim().split(/\s+/).length
  } catch {
    articleHtml.value = ''
  } finally {
    articleLoading.value = false
  }
})

// Links inside the parsed wiki HTML are relative — open them on the wiki
// in a new tab instead of navigating the SPA.
function onArticleClick (e) {
  const a = e.target.closest('a')
  if (!a) return
  e.preventDefault()
  const href = a.getAttribute('href') || ''
  if (!href || href.startsWith('#')) return
  const url = href.startsWith('http')
    ? href : `https://${selected.value.wiki_domain}${href}`
  window.open(url, '_blank', 'noopener')
}

// ---- reviewing --------------------------------------------------------------
function advance () {
  const next = queue.value.find(s => s.id !== selected.value?.id && !myReview(s))
  if (next) selected.value = next
}

async function saveReview (review) {
  error.value = ''
  try {
    await api.submitReview(selected.value.id, review)
    notice.value = `Review saved for “${selected.value.title}”.`
    setTimeout(() => { notice.value = '' }, 2500)
    await load(true)
    advance()
  } catch (e) {
    error.value = errorMessage(e)
  }
}
</script>

<template>
  <div class="full-bleed -mt-6 -mb-6 flex flex-col" style="height: calc(100vh - 3.5rem)">
    <p v-if="!campaign && error" class="text-red-600 dark:text-red-400 p-6">{{ error }}</p>
    <p v-else-if="!campaign" class="text-neutral-600 dark:text-neutral-300 p-6">Loading…</p>
    <p v-else-if="!isJury" class="p-6 text-neutral-600 dark:text-neutral-300">
      Judging is for this campaign's jury members.
      <router-link :to="`/campaigns/${slug}`" class="text-link-700 dark:text-link-400 hover:underline">
        Back to the campaign.</router-link>
    </p>

    <template v-else>
      <!-- top bar: campaign + overall statistics -->
      <header class="flex flex-wrap items-center gap-x-5 gap-y-1 px-4 py-2.5
                     border-b border-neutral-200 dark:border-neutral-800
                     bg-white dark:bg-neutral-900">
        <router-link :to="`/campaigns/${slug}`"
                     class="font-semibold hover:text-link-700 dark:hover:text-link-400">
          ← {{ campaign.name }}
        </router-link>
        <span class="badge bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
          judging
        </span>
        <span class="flex-1"></span>
        <span class="text-sm tabular-nums">
          <b>{{ remaining }}</b> remaining / {{ queue.length }} submissions
          · you reviewed <b>{{ reviewedByMe }}</b>
        </span>
        <span v-if="notice" class="text-sm text-green-700 dark:text-green-400">{{ notice }}</span>
        <span v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</span>
      </header>

      <div class="flex flex-1 min-h-0">
        <!-- left: submission list with per-juror indicators -->
        <aside class="w-80 shrink-0 overflow-y-auto border-r border-neutral-200 dark:border-neutral-800
                      bg-white dark:bg-neutral-900">
          <p v-if="!queue.length" class="p-4 text-sm text-neutral-600 dark:text-neutral-300">
            Nothing to review.
          </p>
          <button v-for="s in queue" :key="s.id" type="button"
                  class="w-full text-left px-3 py-2 border-b border-neutral-100 dark:border-neutral-800
                         hover:bg-neutral-50 dark:hover:bg-neutral-800/60"
                  :class="selected?.id === s.id && 'bg-blue-50 dark:bg-blue-950/40'"
                  @click="selected = s">
            <span class="flex items-center gap-2">
              <!-- one square per juror: green accepted, red rejected, amber needs work -->
              <span class="flex gap-0.5 shrink-0">
                <span v-for="name in juryNames" :key="name"
                      class="w-2.5 h-2.5 rounded-[3px] border border-neutral-300 dark:border-neutral-600"
                      :class="decisionStyles[juryDecision(s, name)]"
                      :title="`${name}: ${juryDecision(s, name) || 'not reviewed'}`"></span>
              </span>
              <span class="truncate text-sm"
                    :class="myReview(s) ? 'text-neutral-400 dark:text-neutral-500'
                                        : 'font-semibold'">
                {{ s.title }}
              </span>
            </span>
            <span class="block text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 pl-0.5">
              {{ s.user.username }}
              <template v-if="s.reviews.length"> · {{ s.reviews.length }} review(s)</template>
            </span>
          </button>
        </aside>

        <!-- right: the article + review bar -->
        <section class="flex-1 min-w-0 flex flex-col">
          <template v-if="selected">
            <div class="flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-2
                        border-b border-neutral-200 dark:border-neutral-800
                        bg-white dark:bg-neutral-900">
              <a :href="selected.url" target="_blank"
                 class="font-semibold text-link-700 dark:text-link-400 hover:underline">
                {{ selected.title }} ↗
              </a>
              <span class="text-xs text-neutral-600 dark:text-neutral-300">
                added by <b>{{ selected.user.username }}</b>
                <template v-if="selected.page_len"> · {{ selected.page_len.toLocaleString() }} bytes</template>
                <template v-if="articleWords"> · ~{{ articleWords.toLocaleString() }} words</template>
                <template v-if="selected.bytes_added"> · +{{ selected.bytes_added.toLocaleString() }} added</template>
              </span>
            </div>

            <!-- wiki content is designed for a light background -->
            <div class="flex-1 overflow-y-auto bg-white text-neutral-900 px-6 py-4"
                 @click="onArticleClick">
              <p v-if="articleLoading" class="text-neutral-500">Loading article…</p>
              <p v-else-if="!articleHtml" class="text-neutral-500">
                Could not load the page here —
                <a :href="selected.url" target="_blank" class="text-link-700 dark:text-link-400 underline">
                  open it on the wiki ↗</a>
              </p>
              <div v-else class="judge-article" v-html="articleHtml"></div>
            </div>

            <!-- bottom bar: review controls -->
            <footer class="border-t border-neutral-200 dark:border-neutral-800
                           bg-white dark:bg-neutral-900 px-4 py-3 max-h-60 overflow-y-auto">
              <div class="flex items-start gap-3">
                <ReviewForm :key="selected.id" class="flex-1"
                            :criteria="criteria" :existing="myReview(selected)"
                            @save="saveReview" />
                <button type="button" class="btn mt-5" title="Next unreviewed submission"
                        @click="advance">Skip →</button>
              </div>
            </footer>
          </template>
          <p v-else class="p-6 text-neutral-600 dark:text-neutral-300">
            Select a submission on the left.
          </p>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* Just enough styling for raw parsed wikitext to read comfortably. */
.judge-article :deep(a) { color: #2563eb; }
.judge-article :deep(h1), .judge-article :deep(h2), .judge-article :deep(h3) {
  font-weight: 700; margin: 0.8em 0 0.4em;
}
.judge-article :deep(h2) { font-size: 1.25rem; border-bottom: 1px solid #e5e5e5; }
.judge-article :deep(p) { margin: 0.5em 0; line-height: 1.65; }
.judge-article :deep(ul), .judge-article :deep(ol) { padding-left: 1.5em; margin: 0.5em 0; list-style: disc; }
.judge-article :deep(img) { max-width: 100%; height: auto; }
.judge-article :deep(table) { border-collapse: collapse; margin: 0.5em 0; max-width: 100%; }
.judge-article :deep(td), .judge-article :deep(th) { border: 1px solid #e5e5e5; padding: 2px 6px; }
.judge-article :deep(.infobox) { float: right; margin: 0 0 1em 1em; max-width: 22rem; font-size: 0.85em; }
.judge-article :deep(.mw-editsection) { display: none; }
</style>
