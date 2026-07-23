<script setup>
import { computed, onMounted, ref } from 'vue'
import { CdxDialog, CdxTable } from '@wikimedia/codex'
import api, { errorMessage } from '../api'
import AppMessage from './AppMessage.vue'

// Modal listing one participant's submissions as a sortable Codex table
// with live wiki details (words/bytes/dates, Wikidata item, file size),
// fetched from the participant-details endpoint on open.
const props = defineProps({
  slug: { type: String, required: true },
  user: { type: Object, required: true }
})
const emit = defineEmits(['close'])

const rows = ref(null)
const error = ref('')
const sort = ref({ points: 'desc' })

onMounted(async () => {
  try {
    rows.value = (await api.participantDetails(props.slug, props.user.id)).data
  } catch (e) {
    error.value = errorMessage(e)
  }
})

const kindLabels = {
  article: 'Article',
  wikidata_item: 'Wikidata item',
  commons_file: 'Commons file',
  wikidata_edits: 'Wikidata edits',
  commons_edits: 'Commons uploads'
}

const columns = [
  { id: 'title', label: 'Title', allowSort: true },
  { id: 'kind', label: 'Type', allowSort: true },
  { id: 'words', label: 'Words', textAlign: 'end', allowSort: true },
  { id: 'bytes', label: 'Bytes', textAlign: 'end', allowSort: true },
  { id: 'created', label: 'Created', allowSort: true },
  { id: 'updated', label: 'Last updated', allowSort: true },
  { id: 'points', label: 'Points', textAlign: 'end', allowSort: true }
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

const sortedData = computed(() => {
  if (!rows.value) return []
  const [key, dir] = Object.entries(sort.value)[0] || ['points', 'desc']
  const mul = dir === 'asc' ? 1 : -1
  return [...rows.value].sort((a, b) => {
    const va = value(a, key)
    const vb = value(b, key)
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    return (va < vb ? -1 : va > vb ? 1 : 0) * mul
  })
})

// CdxTable emits a full sort object; keep a single active sort column.
function onSort (newSort) {
  const active = Object.entries(newSort).find(([, dir]) => dir !== 'none')
  sort.value = active ? { [active[0]]: active[1] } : {}
}

const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString() : '—'
const fmtNum = (n) => n == null ? '—' : n.toLocaleString()
</script>

<template>
  <cdx-dialog :open="true" class="participant-dialog"
              :title="user.username"
              :subtitle="`${rows ? rows.length : '…'} submissions`"
              :use-close-button="true" @update:open="$event || emit('close')">
      <AppMessage v-if="error" v-model="error" type="error" />
      <p v-else-if="!rows" class="text-sm text-neutral-600 dark:text-neutral-300">
        Loading details from the wiki…
      </p>
      <p v-else-if="!rows.length" class="text-sm text-neutral-600 dark:text-neutral-300">
        No submissions.
      </p>

      <cdx-table v-else
                 :caption="`Submissions by ${user.username}`" :hide-caption="true"
                 :columns="columns" :data="sortedData"
                 :sort="sort" @update:sort="onSort">
        <template #item-title="{ item, row: s }">
          <a :href="s.url" target="_blank"
             class="font-medium text-blue-700 dark:text-blue-400 hover:underline">{{ item }}</a>
          <span v-if="s.status === 'rejected'"
                class="badge ml-1 bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300">rejected</span>
          <div class="text-xs mt-0.5 space-x-2">
            <a v-if="s.kind === 'article' && s.details?.qid"
               :href="`https://www.wikidata.org/wiki/${s.details.qid}`" target="_blank"
               class="text-blue-700 dark:text-blue-400 hover:underline">{{ s.details.qid }} ↗</a>
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
        </template>
        <template #item-kind="{ item }">
          <span class="text-xs text-neutral-600 dark:text-neutral-300 whitespace-nowrap">
            {{ kindLabels[item] }}
          </span>
        </template>
        <template #item-words="{ row: s }">
          <span class="tabular-nums">{{ fmtNum(s.details?.words) }}</span>
        </template>
        <template #item-bytes="{ row: s }">
          <span class="tabular-nums">{{ fmtNum(s.details?.bytes ?? s.details?.size) }}</span>
        </template>
        <template #item-created="{ row: s }">
          <span class="whitespace-nowrap">{{ fmtDate(s.details?.created_at || s.details?.uploaded_at) }}</span>
        </template>
        <template #item-updated="{ row: s }">
          <span class="whitespace-nowrap">{{ fmtDate(s.details?.last_updated) }}</span>
        </template>
        <template #item-points="{ item }">
          <span class="tabular-nums font-semibold">{{ item }}</span>
        </template>
      </cdx-table>
  </cdx-dialog>
</template>

<style>
/* Widen the dialog for the submissions table (Codex default is 32rem).
   Unscoped: CdxDialog teleports to <body>, outside scoped-CSS reach. */
.cdx-dialog.participant-dialog {
  max-width: 60rem;
  width: calc(100vw - 2rem);
}
</style>
