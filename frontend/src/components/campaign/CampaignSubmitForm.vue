<script setup>
import { computed, ref, watch } from 'vue'
import api from '../../api'
import LanguageSelect from '../LanguageSelect.vue'
import TitleAutocomplete from '../TitleAutocomplete.vue'
import UserSelect from '../UserSelect.vue'

// Shared "submit contribution" form used by both the Overview tab (as a
// highlighted CTA card) and the Submissions tab (plain working-list card).
const props = defineProps({
  tab: { type: String, required: true },
  campaign: { type: Object, required: true },
  isLoggedIn: { type: Boolean, required: true },
  isOrganizer: { type: Boolean, required: true },
  participantNames: { type: Array, required: true },
  allowWikidataEdits: { type: Boolean, required: true },
  allowCommonsEdits: { type: Boolean, required: true },
  submitWiki: { type: String, required: false, default: '' },
  newUsername: { type: String, required: true },
  newLanguage: { type: String, required: true },
  newKind: { type: String, required: true },
  newTitle: { type: String, required: true }
})
const emit = defineEmits(['update:newUsername', 'update:newLanguage', 'update:newKind', 'update:newTitle', 'submit'])

const isBulkKind = computed(() => ['wikidata_edits', 'commons_edits'].includes(props.newKind))

const vUsername = computed({ get: () => props.newUsername, set: v => emit('update:newUsername', v) })
const vLanguage = computed({ get: () => props.newLanguage, set: v => emit('update:newLanguage', v) })
const vKind = computed({ get: () => props.newKind, set: v => emit('update:newKind', v) })
const vTitle = computed({ get: () => props.newTitle, set: v => emit('update:newTitle', v) })

// Fast client-side existence check from TitleAutocomplete: null = unknown
// (never blocks), true/false = confirmed. Only blocks the button on a
// confirmed miss — the server is still the real, authoritative check.
const titleExists = ref(null)
watch(() => [props.newTitle, props.newKind, props.submitWiki], () => { titleExists.value = null })
</script>

<template>
  <!-- submit form: on the campaign home page and the submissions tab.
       The Overview tab gets a highlighted "Contribute" CTA card; the
       Submissions tab keeps the plain working-list styling. -->
  <div v-if="isLoggedIn && campaign.status === 'active'"
       class="mb-4"
       :class="tab === 'overview'
         ? 'rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/30 p-5'
         : 'card p-4'">
    <h4 v-if="tab === 'overview'" class="text-lg font-bold text-blue-900 dark:text-blue-100 mb-3">
      Contribute to {{ campaign.name }}
    </h4>
    <form class="flex flex-wrap gap-2 items-end" @submit.prevent="emit('submit')">
      <!-- coordinators submit on behalf of a participant -->
      <div v-if="isOrganizer" class="w-56">
        <label class="label">Username</label>
        <UserSelect v-model="vUsername" required :participants="participantNames"
                    title="Coordinators submit on behalf of this participant" />
      </div>
      <!-- project first: it decides where the title is looked up -->
      <div v-if="campaign.settings.multi_language && newKind === 'article'" class="w-56">
        <label class="label">Project (language)</label>
        <LanguageSelect v-model="vLanguage" />
      </div>
      <div v-if="campaign.settings.allow_wikidata_items || campaign.settings.allow_commons_files
                 || allowWikidataEdits || allowCommonsEdits">
        <label class="label">Type</label>
        <select v-model="vKind" class="input">
          <option value="article">Article</option>
          <option v-if="campaign.settings.allow_wikidata_items" value="wikidata_item">Wikidata item</option>
          <option v-if="campaign.settings.allow_commons_files" value="commons_file">Commons file</option>
          <option v-if="allowWikidataEdits" value="wikidata_edits">Wikidata edits (whole period)</option>
          <option v-if="allowCommonsEdits" value="commons_edits">Commons uploads (whole period)</option>
        </select>
      </div>
      <div v-if="!isBulkKind" class="flex-1 min-w-48">
        <label class="label">{{ { article: 'Article title', wikidata_item: 'Item QID', commons_file: 'File name' }[newKind] }}</label>
        <TitleAutocomplete v-model="vTitle" required
                           :wiki="submitWiki" :kind="newKind"
                           :placeholder="{ article: 'Start typing or paste the article title…', wikidata_item: 'Q… or search by label', commons_file: 'File:Example.jpg' }[newKind]"
                           @update:exists="titleExists = $event" />
      </div>
      <p v-else class="flex-1 min-w-48 text-xs text-neutral-600 dark:text-neutral-300 self-center">
        {{ newKind === 'wikidata_edits'
           ? 'Counts the statements and label/description/alias edits made on eligible items during the campaign.'
           : 'Counts the files uploaded and depicts statements added during the campaign.' }}
      </p>
      <button class="btn-primary" type="submit"
              :disabled="!isBulkKind && titleExists === false"
              :title="!isBulkKind && titleExists === false ? 'This title was not found on the selected wiki' : ''">
        Submit your contribution
      </button>
    </form>
  </div>
  <p v-else-if="!isLoggedIn && campaign.status === 'active'"
     class="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
    <a class="text-blue-600 dark:text-blue-400 hover:underline" :href="api.loginUrl">Log in</a>
    to submit your contribution.
  </p>
</template>
