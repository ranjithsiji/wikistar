<script setup>
import { onMounted, ref } from 'vue'
import { CdxDialog } from '@wikimedia/codex'
import api, { errorMessage } from '../api'

// Quick-glance popup: rendered lead section for an article, or
// label/description/claims for a Wikidata item. Fetched once on open.
const props = defineProps({
  submission: { type: Object, required: true }
})
const emit = defineEmits(['close'])

const preview = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    preview.value = (await api.submissionPreview(props.submission.id)).data
  } catch (e) {
    error.value = errorMessage(e)
  }
})
</script>

<template>
  <cdx-dialog :open="true" class="submission-preview-dialog"
              :title="submission.title"
              :subtitle="submission.kind === 'wikidata_item' ? 'Wikidata item' : 'Article preview'"
              :use-close-button="true" @update:open="$event || emit('close')">
    <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
    <div v-else-if="!preview" class="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">
      <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Fetching preview from the wiki…
    </div>

    <!-- article: rendered lead section -->
    <div v-else-if="submission.kind === 'article'"
         class="article-preview text-sm leading-relaxed" v-html="preview.html"></div>

    <!-- wikidata item: label/description/aliases + capped claims -->
    <div v-else class="space-y-3">
      <div>
        <div class="text-lg font-semibold">{{ preview.label || preview.qid }}</div>
        <div v-if="preview.description" class="text-sm text-neutral-600 dark:text-neutral-300">
          {{ preview.description }}
        </div>
        <div v-if="preview.aliases.length" class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
          also known as: {{ preview.aliases.join(', ') }}
        </div>
      </div>
      <table v-if="preview.claims.length" class="w-full text-sm">
        <tbody>
          <tr v-for="c in preview.claims" :key="c.property"
              class="border-t border-neutral-100 dark:border-neutral-800">
            <td class="py-1.5 pr-3 font-medium align-top whitespace-nowrap">{{ c.property }}</td>
            <td class="py-1.5 text-neutral-700 dark:text-neutral-300">{{ c.values.join(', ') }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="preview.claim_count > preview.claims.length"
         class="text-xs text-neutral-500 dark:text-neutral-400">
        + {{ preview.claim_count - preview.claims.length }} more statements — see the full item on Wikidata.
      </p>
      <a :href="submission.url" target="_blank"
         class="text-link-700 dark:text-link-400 hover:underline text-sm">
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
