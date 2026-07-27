<script setup>
import { computed, onMounted, ref } from 'vue'
import { CdxDialog } from '@wikimedia/codex'
import { errorMessage } from '../api'
import LANGUAGES from '../languages'

// Quick-glance popup: rendered lead section for an article, or the full
// statement list for a Wikidata item.
//
// Wikidata items are fetched straight from the browser (action=parse
// serves CORS headers for any origin), so the popup costs the backend
// nothing and shows every statement with resolved labels — the
// wbgetentities path it replaces could only show raw QIDs as values.
// The rendered HTML is Wikidata's own editing UI, so we don't display it
// directly: we pull the property/value pairs out of it and render our
// own rows in the app's styling.
const props = defineProps({
  submission: { type: Object, required: true }
})
const emit = defineEmits(['close'])

const preview = ref(null)     // articles: { html }
const item = ref(null)        // wikidata: { label, description, aliases, groups }
const error = ref('')

// Other-language versions of an article, loaded only when asked for.
const showSitelinks = ref(false)
const sitelinks = ref(null)   // null = not loaded, [] = none exist
const sitelinksLoading = ref(false)
const sitelinksError = ref('')
const sitelinkFilter = ref('')

function text (node) {
  return (node?.textContent || '').replace(/\s+/g, ' ').trim()
}

// Pull label/description/aliases and every statement group out of the
// parsed entity HTML. Structure comes from Wikibase's entityview:
// .wikibase-statementgroupview holds one property, whose values are the
// .wikibase-statementview-mainsnak snaks inside it.
function parseEntity (htmlString) {
  const doc = new DOMParser().parseFromString(htmlString, 'text/html')

  const groups = [...doc.querySelectorAll('.wikibase-statementgroupview')]
    .map(group => {
      const property = text(group.querySelector('.wikibase-statementgroupview-property-label'))
      const values = [...group.querySelectorAll('.wikibase-statementview-mainsnak')]
        .map(snak => {
          const valueNode = snak.querySelector('.wikibase-snakview-value')
          const link = valueNode?.querySelector('a')
          let href = link?.getAttribute('href') || ''
          // Wikidata's HTML uses site-relative /wiki/... links.
          if (href.startsWith('/')) href = `https://www.wikidata.org${href}`
          return { text: text(valueNode), href }
        })
        .filter(v => v.text)
      return { property, values }
    })
    .filter(g => g.property && g.values.length)

  // The parsed HTML carries the description and aliases but not the
  // label — that is the page's display title, returned separately below.
  const aliasBox = doc.querySelector('.wikibase-entitytermsview-heading-aliases')
  return {
    description: text(doc.querySelector('.wikibase-entitytermsview-heading-description')),
    aliases: [...(aliasBox?.querySelectorAll('li, .wikibase-aliasesview-list-item') || [])]
      .map(text).filter(Boolean),
    groups
  }
}

// A campaign's wiki_domain is organizer-supplied and not validated
// server-side, so it is checked here before the browser is pointed at
// it: only Wikimedia project hosts are ever contacted.
const WIKIMEDIA_HOST = /^[a-z0-9-]+(\.[a-z0-9-]+)*\.(wikipedia|wikimedia|wikidata|wikisource|wikibooks|wikiquote|wiktionary|wikinews|wikiversity|wikivoyage|mediawiki)\.org$/

// One shared call for both kinds: action=parse is CORS-enabled on every
// Wikimedia wiki (origin=*), so the popup talks to the wiki directly
// instead of round-tripping through our backend.
async function parsePage (domain, params) {
  if (!WIKIMEDIA_HOST.test(domain)) {
    throw new Error(`${domain} is not a Wikimedia wiki.`)
  }
  const query = new URLSearchParams({
    action: 'parse', format: 'json', formatversion: '2',
    origin: '*', ...params
  })
  const res = await fetch(`https://${domain}/w/api.php?${query}`)
  if (!res.ok) throw new Error(`The wiki returned ${res.status}`)
  const data = await res.json()
  if (data.error) {
    throw new Error(data.error.code === 'missingtitle'
      ? 'Not found on the wiki.'
      : (data.error.info || 'The wiki could not render this page.'))
  }
  return data.parse
}

async function loadWikidataItem (qid) {
  // prop=text|displaytitle in one request: the statements come from the
  // rendered text, the label from the display title.
  const parse = await parsePage('www.wikidata.org',
    { page: qid, prop: 'text|displaytitle' })
  const entity = parseEntity(parse.text)
  const titleDoc = new DOMParser().parseFromString(parse.displaytitle || '', 'text/html')
  entity.label = text(titleDoc.querySelector('.wikibase-title-label'))
  return entity
}

async function loadArticle (domain, title) {
  // Lead section only (section 0) keeps this a quick glance rather than
  // a full mirrored article.
  const parse = await parsePage(domain, {
    page: title, prop: 'text', section: '0',
    disabletoc: '1', disableeditsection: '1'
  })
  return { html: parse.text || '' }
}

// ---- other-language versions ----------------------------------------------
// Sitelink keys ending in "wiki" are Wikipedia language editions, except
// these: Commons is a media repository and the others are meta/internal
// wikis, none of which is a language version of the article.
const NON_LANGUAGE_WIKIS = new Set([
  'commonswiki', 'abstractwiki', 'metawiki', 'specieswiki',
  'sourceswiki', 'mediawikiwiki', 'wikidatawiki', 'incubatorwiki',
  'outreachwiki', 'foundationwiki'
])

// A few editions kept legacy site codes that no longer match their
// language code, so they aren't in languages.js. The domains still
// resolve; only the display name needs filling in.
const LEGACY_WIKIS = {
  als: { name: 'Alemannisch', en: 'Alemannic' },
  'be-x-old': { name: 'беларуская (тарашкевіца)', en: 'Belarusian (Taraškievica)' },
  'zh-min-nan': { name: 'Bân-lâm-gú', en: 'Southern Min' },
  'zh-yue': { name: '粵語', en: 'Cantonese' },
  bat_smg: { name: 'žemaitėška', en: 'Samogitian' },
  fiu_vro: { name: 'võro', en: 'Võro' },
  roa_rup: { name: 'armãneashti', en: 'Aromanian' }
}

// Sitelinks come from the article's connected Wikidata item, so the QID
// has to be resolved first when the submission doesn't already carry one
// (it is captured at submission time, but older rows may predate that or
// the article may have been connected to an item since).
async function resolveQid (domain, title) {
  const query = new URLSearchParams({
    action: 'query', format: 'json', formatversion: '2', origin: '*',
    prop: 'pageprops', ppprop: 'wikibase_item', titles: title
  })
  const res = await fetch(`https://${domain}/w/api.php?${query}`)
  if (!res.ok) throw new Error(`The wiki returned ${res.status}`)
  const page = (await res.json())?.query?.pages?.[0]
  return page?.pageprops?.wikibase_item || ''
}

async function loadSitelinks () {
  if (sitelinks.value || sitelinksLoading.value) return
  sitelinksLoading.value = true
  sitelinksError.value = ''
  try {
    const sub = props.submission
    if (!WIKIMEDIA_HOST.test(sub.wiki_domain)) {
      throw new Error(`${sub.wiki_domain} is not a Wikimedia wiki.`)
    }
    const qid = sub.wikidata_qid || await resolveQid(sub.wiki_domain, sub.title)
    if (!qid) {
      sitelinks.value = []
      return
    }
    const query = new URLSearchParams({
      action: 'wbgetentities', format: 'json', origin: '*',
      ids: qid, props: 'sitelinks'
    })
    const res = await fetch(`https://www.wikidata.org/w/api.php?${query}`)
    if (!res.ok) throw new Error(`Wikidata returned ${res.status}`)
    const data = await res.json()
    if (data.error) throw new Error(data.error.info || 'Wikidata request failed')
    const entity = data.entities?.[qid]
    if (!entity || 'missing' in entity) {
      sitelinks.value = []
      return
    }
    const own = sub.wiki_domain.split('.')[0]
    sitelinks.value = Object.entries(entity.sitelinks || {})
      // Wikipedia language editions only: "<code>wiki". Sister projects
      // end in wikiquote/wikisource/…, while "commonswiki" (a media
      // repository) and "abstractwiki" match the shape but are not
      // language versions of the article.
      .filter(([site]) => /^[a-z0-9_-]+wiki$/.test(site)
                          && !NON_LANGUAGE_WIKIS.has(site))
      .map(([site, link]) => {
        const raw = site.slice(0, -4)
        const code = raw.replace(/_/g, '-')
        const lang = LANGUAGES.find(l => l.code === code)
          || LEGACY_WIKIS[raw] || LEGACY_WIKIS[code]
        return {
          code,
          title: link.title,
          name: lang?.name || code,
          en: lang?.en || '',
          url: `https://${code}.wikipedia.org/wiki/${encodeURIComponent(link.title.replace(/ /g, '_'))}`,
          isOwn: code === own
        }
      })
      // Known languages first (alphabetically by English name), then any
      // edition missing from our list, so nothing is silently dropped.
      .sort((a, b) => (a.en ? 0 : 1) - (b.en ? 0 : 1) ||
                      (a.en || a.code).localeCompare(b.en || b.code))
  } catch (e) {
    sitelinksError.value = e.message || errorMessage(e)
  } finally {
    sitelinksLoading.value = false
  }
}

const shownSitelinks = computed(() => {
  const q = sitelinkFilter.value.trim().toLowerCase()
  if (!q || !sitelinks.value) return sitelinks.value || []
  return sitelinks.value.filter(s =>
    s.code.includes(q) || s.name.toLowerCase().includes(q) ||
    s.en.toLowerCase().includes(q) || s.title.toLowerCase().includes(q))
})

onMounted(async () => {
  const sub = props.submission
  try {
    if (sub.kind === 'wikidata_item') {
      item.value = await loadWikidataItem(sub.title)
    } else {
      preview.value = await loadArticle(sub.wiki_domain, sub.title)
    }
  } catch (e) {
    error.value = e.message || errorMessage(e)
  }
})
</script>

<template>
  <cdx-dialog :open="true" class="submission-preview-dialog"
              :title="submission.title"
              :subtitle="submission.kind === 'wikidata_item' ? 'Wikidata item' : 'Article preview'"
              :use-close-button="true" @update:open="$event || emit('close')">
    <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
    <div v-else-if="!preview && !item"
         class="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">
      <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Fetching preview from the wiki…
    </div>

    <!-- article: rendered lead section, plus other-language versions -->
    <div v-else-if="submission.kind === 'article'">
      <div class="article-preview text-sm leading-relaxed" v-html="preview.html"></div>

      <div class="mt-4 pt-3 border-t border-neutral-200 dark:border-neutral-800">
        <button class="btn !py-1 text-sm"
                @click="showSitelinks = !showSitelinks; showSitelinks && loadSitelinks()">
          {{ showSitelinks ? '▾' : '▸' }} View sitelinks
          <span v-if="sitelinks && sitelinks.length"
                class="badge bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300 ml-1">
            {{ sitelinks.length }}
          </span>
        </button>

        <div v-if="showSitelinks" class="mt-3">
          <p v-if="sitelinksError" class="text-sm text-red-600 dark:text-red-400">
            {{ sitelinksError }}
            <button class="ml-1 underline hover:no-underline" @click="loadSitelinks">
              Try again
            </button>
          </p>
          <p v-else-if="sitelinksLoading" class="text-sm text-neutral-600 dark:text-neutral-300">
            Looking up other language versions…
          </p>
          <p v-else-if="sitelinks && !sitelinks.length"
             class="text-sm text-neutral-600 dark:text-neutral-300">
            This article is not connected to a Wikidata item, so no other
            language versions could be found.
          </p>
          <template v-else-if="sitelinks">
            <input v-model="sitelinkFilter" class="input !w-56 mb-3"
                   placeholder="Filter languages…" />
            <p v-if="!shownSitelinks.length"
               class="text-sm text-neutral-600 dark:text-neutral-300">
              No language matches “{{ sitelinkFilter }}”.
            </p>
            <ul v-else class="grid sm:grid-cols-2 gap-x-4">
              <li v-for="s in shownSitelinks" :key="s.code"
                  class="py-1.5 border-b border-neutral-100 dark:border-neutral-800 min-w-0">
                <a :href="s.url" target="_blank" rel="noopener" class="group block">
                  <span class="text-xs text-neutral-500 dark:text-neutral-400 tabular-nums">
                    {{ s.code }}
                  </span>
                  <span class="ml-1.5 text-sm text-link-700 dark:text-link-400 group-hover:underline">
                    {{ s.title }}
                  </span>
                  <span v-if="s.isOwn"
                        class="badge bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 ml-1.5">
                    this wiki
                  </span>
                  <span class="block text-xs text-neutral-500 dark:text-neutral-400 truncate">
                    {{ s.name }}<template v-if="s.en && s.en !== s.name"> · {{ s.en }}</template>
                  </span>
                </a>
              </li>
            </ul>
          </template>
        </div>
      </div>
    </div>

    <!-- wikidata item: label/description/aliases, then every statement -->
    <div v-else>
      <div class="pb-3 mb-1 border-b border-neutral-200 dark:border-neutral-800">
        <div class="text-lg font-semibold">{{ item.label || submission.title }}</div>
        <div v-if="item.description" class="text-sm text-neutral-600 dark:text-neutral-300">
          {{ item.description }}
        </div>
        <div v-if="item.aliases.length" class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
          also known as: {{ item.aliases.join(' · ') }}
        </div>
      </div>

      <p v-if="!item.groups.length" class="text-sm text-neutral-600 dark:text-neutral-300 py-2">
        This item has no statements yet.
      </p>

      <dl v-else>
        <div v-for="g in item.groups" :key="g.property"
             class="grid sm:grid-cols-[11rem_1fr] gap-x-4 gap-y-0.5 py-2
                    border-b border-neutral-100 dark:border-neutral-800 last:border-0">
          <dt class="text-xs font-semibold uppercase tracking-wide
                     text-neutral-500 dark:text-neutral-400 pt-0.5">
            {{ g.property }}
          </dt>
          <dd class="text-sm space-y-0.5 min-w-0">
            <div v-for="(v, i) in g.values" :key="i" class="break-words">
              <a v-if="v.href" :href="v.href" target="_blank" rel="noopener"
                 class="text-link-700 dark:text-link-400 hover:underline">{{ v.text }}</a>
              <span v-else>{{ v.text }}</span>
            </div>
          </dd>
        </div>
      </dl>

      <a :href="submission.url" target="_blank" rel="noopener"
         class="inline-block mt-3 text-link-700 dark:text-link-400 hover:underline text-sm">
        View full item on Wikidata ↗</a>
    </div>
  </cdx-dialog>
</template>

<style>
/* Widen the dialog for the preview content. Unscoped: CdxDialog
   teleports to <body>, outside scoped-CSS reach. */
.cdx-dialog.submission-preview-dialog {
  max-width: 42rem;
  width: calc(100vw - 2rem);
}
/* A full item can carry hundreds of statements — keep the popup itself a
   sane height and scroll the body rather than growing past the viewport. */
.cdx-dialog.submission-preview-dialog .cdx-dialog__body {
  max-height: min(65vh, 40rem);
  overflow-y: auto;
  overscroll-behavior: contain;
}
.cdx-dialog.submission-preview-dialog .article-preview img {
  max-width: 100%;
  height: auto;
}
.cdx-dialog.submission-preview-dialog .article-preview p {
  margin-bottom: 0.75em;
}
.cdx-dialog.submission-preview-dialog .article-preview a {
  color: var(--color-link-700, #1d4fd8);
  text-decoration: underline;
}
.cdx-dialog.submission-preview-dialog .article-preview table {
  max-width: 100%;
}
/* Wikipedia's own infobox/hatnote/navbox chrome doesn't fit a small
   popup — hide it and show only the plain lead prose. */
.cdx-dialog.submission-preview-dialog .article-preview .infobox,
.cdx-dialog.submission-preview-dialog .article-preview .navbox,
.cdx-dialog.submission-preview-dialog .article-preview .hatnote,
.cdx-dialog.submission-preview-dialog .article-preview .ambox,
.cdx-dialog.submission-preview-dialog .article-preview .metadata,
.cdx-dialog.submission-preview-dialog .article-preview sup.reference {
  display: none;
}
</style>
