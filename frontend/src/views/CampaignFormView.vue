<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { errorMessage } from '../api'
import RuleEditor from '../components/RuleEditor.vue'
import SettingsEditor from '../components/SettingsEditor.vue'

const props = defineProps({ slug: { type: String, default: null } })
const router = useRouter()

const meta = ref(null)
const error = ref('')
const saving = ref(false)
const section = ref('general')
const sections = [
  ['general', 'General'],
  ['scoring', 'Scoring rules'],
  ['settings', 'Settings'],
  ['people', 'Jury & suggested pages']
]

const form = reactive({
  name: '', slug: '', description: '', language: 'en', wiki_domain: '',
  start_date: '', end_date: '', scoring_mode: 'jury', status: null,
  settings: {}, rules: [], jury_usernames: [],
  suggested_articles: [], suggested_items: []
})
const juryText = ref('')
const suggestedArticlesText = ref('')
const suggestedItemsText = ref('')

onMounted(async () => {
  try {
    meta.value = (await api.meta()).data
    // start from registry defaults
    for (const [key, spec] of Object.entries(meta.value.settings_registry)) {
      form.settings[key] = spec.default
    }
    if (props.slug) {
      const c = (await api.getCampaign(props.slug)).data
      Object.assign(form, {
        name: c.name, slug: c.slug, description: c.description || '',
        language: c.language, wiki_domain: c.wiki_domain,
        start_date: c.start_date, end_date: c.end_date,
        scoring_mode: c.scoring_mode, status: c.status,
        settings: { ...form.settings, ...c.settings },
        rules: c.rules.map(r => ({ ...r })),
        suggested_articles: c.suggested_articles,
        suggested_items: c.suggested_items
      })
      juryText.value = c.members.filter(m => m.role === 'jury')
        .map(m => m.user.username).join('\n')
      suggestedArticlesText.value = c.suggested_articles.join('\n')
      suggestedItemsText.value = c.suggested_items.join('\n')
    }
  } catch (e) {
    error.value = errorMessage(e)
  }
})

function splitLines (text) {
  return text.split('\n').map(s => s.trim()).filter(Boolean)
}

async function save () {
  saving.value = true
  error.value = ''
  const payload = {
    ...form,
    slug: form.slug || null,
    wiki_domain: form.wiki_domain || null,
    jury_usernames: splitLines(juryText.value),
    suggested_articles: splitLines(suggestedArticlesText.value),
    suggested_items: splitLines(suggestedItemsText.value)
  }
  try {
    const { data } = props.slug
      ? await api.updateCampaign(props.slug, payload)
      : await api.createCampaign(payload)
    router.push(`/campaigns/${data.slug}`)
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-if="meta">
    <h1 class="text-2xl font-bold mb-1">{{ slug ? 'Edit campaign' : 'Create campaign' }}</h1>
    <p v-if="!slug" class="text-sm text-neutral-500 mb-4">
      New campaigns start as drafts. They go live immediately if you hold
      admin (sysop) rights on the target wiki (jury mode) or on any
      Wikipedia project (self-assessment); otherwise a wiki admin must
      approve the campaign.
    </p>

    <div class="flex gap-1 border-b border-neutral-200 dark:border-neutral-800 mb-4 overflow-x-auto">
      <button v-for="[key, label] in sections" :key="key" class="tab"
              :class="{ 'tab-active': section === key }" @click="section = key">
        {{ label }}
      </button>
    </div>

    <form @submit.prevent="save">
      <div v-show="section === 'general'" class="card p-4 grid gap-4 sm:grid-cols-2">
        <div class="sm:col-span-2">
          <label class="label">Name *</label>
          <input v-model="form.name" class="input" required minlength="3" />
        </div>
        <div>
          <label class="label">URL slug</label>
          <input v-model="form.slug" class="input" pattern="[a-z0-9][a-z0-9_-]*"
                 placeholder="auto-generated from name" />
        </div>
        <div>
          <label class="label">Scoring mode</label>
          <select v-model="form.scoring_mode" class="input">
            <option value="jury">Jury — judges score every submission</option>
            <option value="self">Self-assessment — participants claim points</option>
            <option value="hybrid">Hybrid — claims verified by jury</option>
          </select>
        </div>
        <div>
          <label class="label">Start date *</label>
          <input v-model="form.start_date" type="date" class="input" required />
        </div>
        <div>
          <label class="label">End date *</label>
          <input v-model="form.end_date" type="date" class="input" required />
        </div>
        <div>
          <label class="label">Wiki language code</label>
          <input v-model="form.language" class="input" placeholder="en" />
        </div>
        <div>
          <label class="label">Wiki domain</label>
          <input v-model="form.wiki_domain" class="input"
                 :placeholder="`${form.language || 'en'}.wikipedia.org`" />
        </div>
        <div class="sm:col-span-2">
          <label class="label">Description</label>
          <textarea v-model="form.description" class="input" rows="4"
                    placeholder="Goals, rules and prizes of the campaign"></textarea>
        </div>
      </div>

      <div v-show="section === 'scoring'">
        <RuleEditor v-model="form.rules" :default-rules="meta.default_rules.self" />
      </div>

      <div v-show="section === 'settings'">
        <SettingsEditor v-model="form.settings" :registry="meta.settings_registry" />
      </div>

      <div v-show="section === 'people'" class="grid gap-4 md:grid-cols-3">
        <div class="card p-4">
          <label class="label">Jury members (one username per line)</label>
          <textarea v-model="juryText" class="input font-mono" rows="8"></textarea>
        </div>
        <div class="card p-4">
          <label class="label">Suggested articles (one title per line)</label>
          <textarea v-model="suggestedArticlesText" class="input font-mono" rows="8"></textarea>
        </div>
        <div class="card p-4">
          <label class="label">Suggested Wikidata items (one QID per line)</label>
          <textarea v-model="suggestedItemsText" class="input font-mono" rows="8"></textarea>
        </div>
      </div>

      <p v-if="error" class="text-red-600 dark:text-red-400 text-sm mt-3">{{ error }}</p>
      <div class="mt-4 flex gap-2">
        <button type="submit" class="btn-primary" :disabled="saving">
          {{ saving ? 'Saving…' : (slug ? 'Save changes' : 'Create campaign') }}
        </button>
        <router-link class="btn" :to="slug ? `/campaigns/${slug}` : '/'">Cancel</router-link>
      </div>
    </form>
  </div>
  <p v-else-if="error" class="text-red-600 dark:text-red-400">{{ error }}</p>
  <p v-else class="text-neutral-500">Loading…</p>
</template>
