<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import api, { errorMessage } from '../../api'
import LanguageSelect from '../LanguageSelect.vue'

const props = defineProps({
  slug: { type: String, required: true },
  campaign: { type: Object, required: true }
})
const emit = defineEmits(['error'])

// Tab structure (heading -> QIDs) comes straight from the campaign
// payload — already loaded, no Wikidata round-trip needed just to know
// what headings exist. Sitelinks (labels/links, the slow part) are
// fetched lazily, one heading at a time, only for the section being
// viewed — a big suggested list no longer means resolving every item on
// every visit or on every "add language" click.
const suggestedSections = computed(() => {
  const order = []
  const byHeading = new Map()
  for (const item of props.campaign?.suggested_items || []) {
    const h = item.section || ''
    if (!byHeading.has(h)) { byHeading.set(h, []); order.push(h) }
    byHeading.get(h).push(item.qid)
  }
  return order.map(h => ({ heading: h, qids: byHeading.get(h) }))
})
const activeSection = ref('')
watch(suggestedSections, (secs) => {
  if (secs.length && !secs.some(s => s.heading === activeSection.value)) {
    activeSection.value = secs[0].heading
  }
})

// Resolved sitelinks per heading: { languages, items } | 'loading' | 'error'.
const sectionCache = ref({})
const activeSectionData = computed(() => {
  const v = sectionCache.value[activeSection.value]
  return (v && v !== 'loading' && v !== 'error') ? v : null
})
const activeSectionLoading = computed(() =>
  sectionCache.value[activeSection.value] === 'loading')
const activeSectionFailed = computed(() =>
  sectionCache.value[activeSection.value] === 'error')

async function loadSection (heading, extraLangs = []) {
  const sec = suggestedSections.value.find(s => s.heading === heading)
  if (!sec) return
  const prior = sectionCache.value[heading]
  const priorLangs = (prior && prior !== 'loading' && prior !== 'error')
    ? prior.languages : []
  const langs = [...new Set([...priorLangs, ...extraLangs])]
  sectionCache.value = { ...sectionCache.value, [heading]: 'loading' }
  try {
    const { data } = await api.suggestedLinks(props.slug,
      langs.length ? langs : null, sec.qids)
    sectionCache.value = { ...sectionCache.value, [heading]: data }
  } catch (e) {
    sectionCache.value = { ...sectionCache.value, [heading]: 'error' }
    emit('error', errorMessage(e))
  }
}
// Fetch whichever heading becomes active, the first time it's viewed.
watch(activeSection, (h) => {
  if (h && !sectionCache.value[h]) loadSection(h)
}, { immediate: true })

// Suggested-items table: English first, then the preference languages
// (the backend always includes "en" in the response).
const suggestedLangs = computed(() => {
  const langs = activeSectionData.value?.languages || []
  return ['en', ...langs.filter(l => l !== 'en')]
})
const itemLink = (item, lang) => item.links.find(l => l.lang === lang)
const shownSectionItems = computed(() => activeSectionData.value?.items || [])

// Two heading layouts, user-switchable (remembered per device):
//   all      — every heading as a wrapped label button (default)
//   compact  — hamburger menu on the left + at most three tabs
const sectionViewMode = ref(localStorage.getItem('suggestedSectionsView') || 'all')
function toggleSectionView () {
  sectionViewMode.value = sectionViewMode.value === 'all' ? 'compact' : 'all'
  localStorage.setItem('suggestedSectionsView', sectionViewMode.value)
}
const MAX_SECTION_TABS = 3
const sectionMenuOpen = ref(false)
const sectionMenuRoot = ref(null)
const visibleSections = computed(() => {
  const secs = suggestedSections.value
  if (secs.length <= MAX_SECTION_TABS) return secs
  const vis = secs.slice(0, MAX_SECTION_TABS)
  if (!vis.some(s => s.heading === activeSection.value)) {
    const active = secs.find(s => s.heading === activeSection.value)
    if (active) vis[MAX_SECTION_TABS - 1] = active
  }
  return vis
})
function onSectionMenuDocClick (e) {
  if (sectionMenuRoot.value && !sectionMenuRoot.value.contains(e.target)) {
    sectionMenuOpen.value = false
  }
}
onMounted(() => document.addEventListener('click', onSectionMenuDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onSectionMenuDocClick))

// Add an extra language column to the suggested-items table on the fly —
// re-resolves only the active heading's items, not the whole suggested
// list, so this stays fast even with many headings/items.
const addingLang = ref('')
async function addSuggestedLang () {
  const code = addingLang.value
  if (!code || !activeSection.value) return
  addingLang.value = ''
  await loadSection(activeSection.value, [code])
}
// Red-link style "start this article" URL, prefilled with the English title.
function createUrl (item, lang) {
  const title = (item.label_en || item.qid).replaceAll(' ', '_')
  return `https://${lang}.wikipedia.org/w/index.php?title=${encodeURIComponent(title)}&action=edit&redlink=1`
}
</script>

<template>
  <div class="space-y-4">
    <div class="card p-4" v-if="campaign.suggested_articles.length">
      <h4 class="font-semibold text-sm mb-2">Suggested articles (bonus points)</h4>
      <ul class="space-y-1 text-sm list-disc pl-5 sm:columns-2 lg:columns-3">
        <li v-for="t in campaign.suggested_articles" :key="t">
          <a target="_blank"
             :href="`https://${campaign.wiki_domain}/wiki/${t.replaceAll(' ', '_')}`"
             class="text-blue-700 dark:text-blue-400 hover:underline">{{ t }}</a>
        </li>
      </ul>
    </div>
    <div class="card" v-if="campaign.suggested_items.length">
      <div class="px-4 pt-4">
        <h4 class="font-semibold text-sm">Suggested Wikidata items (bonus points)</h4>
      </div>

      <!-- separate, highlighted block: add a language to check article coverage -->
      <div class="mx-4 mt-3 rounded-lg border border-blue-200 dark:border-blue-900
                  bg-blue-50 dark:bg-blue-950/40 p-3">
        <p class="text-xs text-blue-900 dark:text-blue-200 mb-2">
          Add a language to check whether an article on each suggested item
          in the current tab already exists in that language, and get a
          direct link to create it if not.
        </p>
        <form class="flex flex-wrap items-center gap-2" @submit.prevent="addSuggestedLang">
          <LanguageSelect v-model="addingLang" class="!w-56" placeholder="Add a language…" />
          <button class="btn-primary"
                  :disabled="!addingLang || activeSectionLoading
                    || (activeSectionData?.languages.length || 0) >= 10">
            Add language
          </button>
          <span v-if="activeSectionLoading"
                class="inline-flex items-center gap-1.5 text-xs text-blue-800 dark:text-blue-300">
            <svg class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Checking Wikidata for this tab…
          </span>
        </form>
      </div>
      <div class="mt-2">
        <!-- heading picker: all headings as buttons (default), or a
             compact bar with a hamburger menu on the left -->
        <template v-if="suggestedSections.length > 1 || suggestedSections[0]?.heading">
          <!-- all headings, wrapped -->
          <div v-if="sectionViewMode === 'all'"
               class="flex flex-wrap items-center gap-2 px-4 py-3
                      border-b border-neutral-200 dark:border-neutral-800">
            <button v-for="sec in suggestedSections" :key="sec.heading" type="button"
                    class="rounded-full border px-3 py-1 text-sm font-medium transition-colors"
                    :class="activeSection === sec.heading
                      ? 'bg-blue-700 border-blue-700 text-white'
                      : 'border-neutral-300 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800'"
                    @click="activeSection = sec.heading">
              {{ sec.heading || 'General' }}
              <span :class="activeSection === sec.heading
                      ? 'text-blue-100' : 'text-neutral-400 dark:text-neutral-500'"
                    class="text-xs">({{ sec.qids.length }})</span>
            </button>
            <span class="flex-1"></span>
            <button type="button" class="btn !px-2 !py-1 shrink-0"
                    title="Switch to the compact menu view" @click="toggleSectionView">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="2" stroke-linecap="round">
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>

          <!-- compact: hamburger on the left + up to three tabs -->
          <div v-else class="flex items-center gap-1 px-3
                             border-b border-neutral-200 dark:border-neutral-800">
            <div v-if="suggestedSections.length > MAX_SECTION_TABS"
                 ref="sectionMenuRoot" class="relative">
              <button type="button" class="tab !px-2" :aria-expanded="sectionMenuOpen"
                      title="All headings" @click="sectionMenuOpen = !sectionMenuOpen">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round">
                  <path d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div v-if="sectionMenuOpen"
                   class="absolute left-0 mt-1 w-60 card shadow-lg py-1 z-20 max-h-72 overflow-y-auto">
                <button v-for="sec in suggestedSections" :key="sec.heading" type="button"
                        class="block w-full text-left px-3 py-1.5 text-sm
                               hover:bg-neutral-100 dark:hover:bg-neutral-800"
                        :class="activeSection === sec.heading
                          && 'font-semibold text-blue-700 dark:text-blue-400'"
                        @click="activeSection = sec.heading; sectionMenuOpen = false">
                  {{ sec.heading || 'General' }}
                  <span class="text-xs text-neutral-400 dark:text-neutral-500">
                    ({{ sec.qids.length }})</span>
                </button>
              </div>
            </div>
            <button v-for="sec in visibleSections" :key="sec.heading" type="button"
                    class="tab" :class="{ 'tab-active': activeSection === sec.heading }"
                    @click="activeSection = sec.heading">
              {{ sec.heading || 'General' }}
              <span class="text-xs text-neutral-400 dark:text-neutral-500">({{ sec.qids.length }})</span>
            </button>
            <span class="flex-1"></span>
            <button type="button" class="btn !px-2 !py-1 shrink-0"
                    title="Show all headings as buttons" @click="toggleSectionView">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </button>
          </div>
        </template>
        <!-- loading: this heading's sitelinks are being resolved -->
        <div v-if="activeSectionLoading" class="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300 p-4">
          <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Checking Wikidata and Wikipedia for this tab…
        </div>

        <!-- error: fall back to plain QID links for this heading -->
        <div v-else-if="activeSectionFailed" class="p-4 space-y-2">
          <p class="text-xs text-red-600 dark:text-red-400">
            Could not check article coverage for this tab. Showing the raw items instead.
          </p>
          <div class="flex flex-wrap gap-1.5">
            <a v-for="qid in (suggestedSections.find(s => s.heading === activeSection)?.qids || [])"
               :key="qid" target="_blank" :href="`https://www.wikidata.org/wiki/${qid}`"
               class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300 hover:underline">{{ qid }}</a>
          </div>
        </div>

        <template v-else>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-neutral-200 dark:border-neutral-800">
                  <th class="th pl-4">Item</th>
                  <th class="th">Label (English)</th>
                  <th v-for="lang in suggestedLangs" :key="lang" class="th text-center">
                    {{ lang }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in shownSectionItems" :key="item.qid"
                    class="border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                  <td class="td pl-4">
                    <a :href="`https://www.wikidata.org/wiki/${item.qid}`" target="_blank"
                       class="badge bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300 hover:underline">
                      {{ item.qid }}
                    </a>
                  </td>
                  <td class="td font-medium">{{ item.label_en || item.label || '—' }}</td>
                  <td v-for="lang in suggestedLangs" :key="lang" class="td text-center">
                    <!-- exists: link to the article -->
                    <a v-if="itemLink(item, lang)" :href="itemLink(item, lang).url"
                       target="_blank" :title="`${itemLink(item, lang).title} — read on ${lang}.wikipedia.org`"
                       class="inline-flex items-center justify-center w-6 h-6 rounded-full
                              bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300
                              hover:ring-2 hover:ring-green-400">
                      <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                           stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m5 13 4 4L19 7" />
                      </svg>
                    </a>
                    <!-- missing: start it -->
                    <a v-else :href="createUrl(item, lang)" target="_blank"
                       :title="`Not on ${lang}.wikipedia.org yet — start this article`"
                       class="inline-flex items-center justify-center w-6 h-6 rounded-full
                              bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400
                              hover:bg-blue-100 hover:text-blue-700 dark:hover:bg-blue-950 dark:hover:text-blue-300">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="3" stroke-linecap="round">
                          <path d="M12 5v14m-7-7h14" />
                        </svg>
                      </a>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-xs text-neutral-500 dark:text-neutral-400 px-4 py-3">
            ✓ the article exists — click to read it; + it is missing — click to
            start it. Language columns come from
            <router-link to="/preferences" class="text-blue-600 dark:text-blue-400 hover:underline">
              your preferred languages</router-link>.
          </p>
        </template>
      </div>
    </div>
  </div>
</template>
