<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'

// Modal listing one participant's submissions as a sortable table with
// live wiki details (words/bytes/dates, Wikidata item, file size),
// fetched from the participant-details endpoint on open.
const props = defineProps({
  slug: { type: String, required: true },
  user: { type: Object, required: true }
})
const emit = defineEmits(['close'])

const rows = ref(null)
const error = ref('')
const sortKey = ref('points')
const sortDir = ref(-1)          // 1 asc, -1 desc

onMounted(async () => {
  document.addEventListener('keydown', onKey)
  try {
    rows.value = (await api.participantDetails(props.slug, props.user.id)).data
  } catch (e) {
    error.value = errorMessage(e)
  }
})
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
const onKey = (e) => { if (e.key === 'Escape') emit('close') }

const kindLabels = {
  article: 'Article',
  wikidata_item: 'Wikidata item',
  commons_file: 'Commons file',
  wikidata_edits: 'Wikidata edits',
  commons_edits: 'Commons uploads'
}

const columns = [
  { key: 'title', label: 'Title', align: 'text-left' },
  { key: 'kind', label: 'Type', align: 'text-left' },
  { key: 'words', label: 'Words', align: 'text-right' },
  { key: 'bytes', label: 'Bytes', align: 'text-right' },
  { key: 'created', label: 'Created', align: 'text-left' },
  { key: 'updated', label: 'Last updated', align: 'text-left' },
  { key: 'points', label: 'Points', align: 'text-right' }
]

// Sort accessors; missing values sort to the bottom in either direction.
const value = (s, key) => ({
  title: s.title.toLowerCase(),
  kind: s.kind,
  words: s.details?.words ?? null,
  bytes: s.details?.bytes ?? s.details?.size ?? null,
  created: s.details?.created_at || s.details?.uploaded_at || null,
  updated: s.details?.last_updated || null,
  points: s.points
}[key])

const sorted = computed(() => {
  if (!rows.value) return []
  return [...rows.value].sort((a, b) => {
    const va = value(a, sortKey.value)
    const vb = value(b, sortKey.value)
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    return (va < vb ? -1 : va > vb ? 1 : 0) * sortDir.value
  })
})

function sortBy (key) {
  if (sortKey.value === key) sortDir.value = -sortDir.value
  else { sortKey.value = key; sortDir.value = key === 'title' || key === 'kind' ? 1 : -1 }
}

const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString() : '—'
const fmtNum = (n) => n == null ? '—' : n.toLocaleString()
</script>

<template>
  <div class="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto
              bg-black/50 p-4 sm:py-10" @click.self="emit('close')">
    <div class="card w-full max-w-4xl shadow-xl">
      <div class="flex items-center gap-3 px-5 py-4 border-b border-neutral-200 dark:border-neutral-800">
        <h3 class="font-semibold text-lg flex-1">
          {{ user.username }}
          <span class="text-sm font-normal text-neutral-600 dark:text-neutral-300">
            — {{ rows ? rows.length : '…' }} submissions</span>
        </h3>
        <button class="btn !px-2" aria-label="Close" @click="emit('close')">✕</button>
      </div>

      <p v-if="error" class="text-red-600 dark:text-red-400 text-sm p-5">{{ error }}</p>
      <p v-else-if="!rows" class="text-sm text-neutral-600 dark:text-neutral-300 p-5">
        Loading details from the wiki…
      </p>
      <p v-else-if="!rows.length" class="text-sm text-neutral-600 dark:text-neutral-300 p-5">
        No submissions.
      </p>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-neutral-200 dark:border-neutral-800">
              <th v-for="col in columns" :key="col.key" class="th first:pl-5 last:pr-5"
                  :class="col.align">
                <button type="button"
                        class="inline-flex items-center gap-1 uppercase tracking-wide cursor-pointer
                               hover:text-neutral-900 dark:hover:text-neutral-100"
                        :title="`Sort by ${col.label}`" @click="sortBy(col.key)">
                  {{ col.label }}
                  <span v-if="sortKey === col.key">{{ sortDir === 1 ? '▲' : '▼' }}</span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in sorted" :key="s.id"
                class="border-b border-neutral-100 dark:border-neutral-800 last:border-0 align-top">
              <td class="td pl-5 max-w-64">
                <a :href="s.url" target="_blank"
                   class="font-medium text-blue-700 dark:text-blue-400 hover:underline">{{ s.title }}</a>
                <span v-if="s.status === 'rejected'"
                      class="badge ml-1 bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300">rejected</span>
                <div class="text-xs mt-0.5 space-x-2">
                  <a v-if="s.kind === 'article' && s.details?.qid"
                     :href="`https://www.wikidata.org/wiki/${s.details.qid}`" target="_blank"
                     class="text-violet-700 dark:text-violet-400 hover:underline">{{ s.details.qid }} ↗</a>
                  <span v-if="s.kind === 'wikidata_item' && s.details?.label"
                        class="text-neutral-600 dark:text-neutral-300">{{ s.details.label }}</span>
                  <span v-if="s.kind === 'commons_file' && s.details?.uploader"
                        class="text-neutral-600 dark:text-neutral-300">by {{ s.details.uploader }}</span>
                  <span v-if="s.kind === 'wikidata_edits' && s.details && !s.details.over_limit"
                        class="text-neutral-600 dark:text-neutral-300">
                    {{ s.details.statements }} statements,
                    {{ s.details.terms }} terms on
                    {{ (s.details.eligible_qids || []).length }} eligible items</span>
                  <span v-if="s.kind === 'commons_edits' && s.details && !s.details.over_limit"
                        class="text-neutral-600 dark:text-neutral-300">
                    {{ s.details.uploads }} uploads, {{ s.details.depicts }} depicts</span>
                  <span v-if="s.details?.over_limit"
                        class="text-amber-700 dark:text-amber-400">
                    over {{ s.details.limit }} edits — scored manually</span>
                  <a v-if="s.kind === 'commons_file' && s.details?.file_url"
                     :href="s.details.file_url" target="_blank"
                     class="text-blue-600 dark:text-blue-400 hover:underline">file ↗</a>
                  <span v-if="s.fetch_failed" class="text-red-600 dark:text-red-400">
                    wiki details unavailable</span>
                  <span v-else-if="!s.details" class="text-neutral-500 dark:text-neutral-400">
                    not found on the wiki</span>
                </div>
              </td>
              <td class="td text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap">
                {{ kindLabels[s.kind] }}
              </td>
              <td class="td text-right tabular-nums">{{ fmtNum(s.details?.words) }}</td>
              <td class="td text-right tabular-nums">{{ fmtNum(s.details?.bytes ?? s.details?.size) }}</td>
              <td class="td whitespace-nowrap">{{ fmtDate(s.details?.created_at || s.details?.uploaded_at) }}</td>
              <td class="td whitespace-nowrap">{{ fmtDate(s.details?.last_updated) }}</td>
              <td class="td pr-5 text-right tabular-nums font-semibold">{{ s.points }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
