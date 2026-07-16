<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'

// Modal listing one participant's submissions with live wiki details
// (words/bytes/dates for articles, label for items, size/uploader for
// files), fetched from the participant-details endpoint on open.
const props = defineProps({
  slug: { type: String, required: true },
  user: { type: Object, required: true }
})
const emit = defineEmits(['close'])

const rows = ref(null)
const error = ref('')

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

const kindLabels = { article: 'Article', wikidata_item: 'Wikidata item', commons_file: 'Commons file' }
const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString() : '—'
const fmtNum = (n) => n == null ? '—' : n.toLocaleString()
const fmtSize = (bytes) => {
  if (bytes == null) return '—'
  if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} bytes`
}
</script>

<template>
  <div class="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto
              bg-black/50 p-4 sm:py-10" @click.self="emit('close')">
    <div class="card w-full max-w-2xl shadow-xl">
      <div class="flex items-center gap-3 px-5 py-4 border-b border-neutral-200 dark:border-neutral-800">
        <h3 class="font-semibold text-lg flex-1">
          {{ user.username }}
          <span class="text-sm font-normal text-neutral-600 dark:text-neutral-300">
            — {{ rows ? rows.length : '…' }} submissions</span>
        </h3>
        <button class="btn !px-2" aria-label="Close" @click="emit('close')">✕</button>
      </div>

      <div class="p-5 space-y-3">
        <p v-if="error" class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
        <p v-else-if="!rows" class="text-sm text-neutral-600 dark:text-neutral-300">
          Loading details from the wiki…
        </p>
        <p v-else-if="!rows.length" class="text-sm text-neutral-600 dark:text-neutral-300">
          No submissions.
        </p>

        <div v-for="s in rows" :key="s.id"
             class="border border-neutral-200 dark:border-neutral-800 rounded-lg p-3">
          <div class="flex flex-wrap items-baseline gap-2">
            <a :href="s.url" target="_blank"
               class="font-medium text-blue-700 dark:text-blue-400 hover:underline">{{ s.title }}</a>
            <span class="badge bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              {{ kindLabels[s.kind] }}
            </span>
            <span v-if="s.status === 'rejected'"
                  class="badge bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300">rejected</span>
            <span class="flex-1"></span>
            <span class="font-semibold tabular-nums">{{ s.points }}
              <span class="text-xs font-normal text-neutral-600 dark:text-neutral-300">pts</span></span>
          </div>

          <p v-if="s.fetch_failed" class="text-xs text-red-600 dark:text-red-400 mt-2">
            Could not load wiki details right now.
          </p>
          <p v-else-if="!s.details" class="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
            Page not found on the wiki.
          </p>

          <!-- article -->
          <dl v-else-if="s.kind === 'article'"
              class="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-1.5 text-sm">
            <div><dt class="label !mb-0">Words</dt><dd class="tabular-nums">{{ fmtNum(s.details.words) }}</dd></div>
            <div><dt class="label !mb-0">Bytes</dt><dd class="tabular-nums">{{ fmtNum(s.details.bytes) }}</dd></div>
            <div><dt class="label !mb-0">Created</dt><dd>{{ fmtDate(s.details.created_at) }}</dd></div>
            <div><dt class="label !mb-0">Last updated</dt><dd>{{ fmtDate(s.details.last_updated) }}</dd></div>
            <div class="col-span-2 sm:col-span-4 flex flex-wrap gap-3 text-xs mt-0.5">
              <a :href="s.url" target="_blank"
                 class="text-blue-600 dark:text-blue-400 hover:underline">Read the article ↗</a>
              <a v-if="s.details.qid" :href="`https://www.wikidata.org/wiki/${s.details.qid}`" target="_blank"
                 class="text-violet-700 dark:text-violet-400 hover:underline">
                Wikidata item {{ s.details.qid }} ↗</a>
            </div>
          </dl>

          <!-- wikidata item -->
          <dl v-else-if="s.kind === 'wikidata_item'"
              class="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-1.5 text-sm">
            <div><dt class="label !mb-0">Item</dt><dd>{{ s.details.qid }}</dd></div>
            <div><dt class="label !mb-0">Label</dt><dd class="truncate" :title="s.details.label">{{ s.details.label || '—' }}</dd></div>
            <div><dt class="label !mb-0">Total bytes</dt><dd class="tabular-nums">{{ fmtNum(s.details.bytes) }}</dd></div>
            <div><dt class="label !mb-0">Created</dt><dd>{{ fmtDate(s.details.created_at) }}</dd></div>
            <div class="col-span-2 sm:col-span-4 text-xs mt-0.5">
              <a :href="s.url" target="_blank"
                 class="text-violet-700 dark:text-violet-400 hover:underline">View on Wikidata ↗</a>
            </div>
          </dl>

          <!-- commons file -->
          <dl v-else class="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-1.5 text-sm">
            <div class="col-span-2"><dt class="label !mb-0">File name</dt>
              <dd class="truncate" :title="s.title">{{ s.title }}</dd></div>
            <div><dt class="label !mb-0">Size</dt><dd>{{ fmtSize(s.details.size) }}</dd></div>
            <div><dt class="label !mb-0">Uploader</dt><dd class="truncate">{{ s.details.uploader || '—' }}</dd></div>
            <div class="col-span-2 sm:col-span-4 flex flex-wrap gap-3 text-xs mt-0.5">
              <a :href="s.url" target="_blank"
                 class="text-blue-600 dark:text-blue-400 hover:underline">File page on Commons ↗</a>
              <a v-if="s.details.file_url" :href="s.details.file_url" target="_blank"
                 class="text-blue-600 dark:text-blue-400 hover:underline">Original file ↗</a>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>
