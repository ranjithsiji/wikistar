<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api, { errorMessage } from '../api'
import LanguageSelect from '../components/LanguageSelect.vue'
import MarksEditor from '../components/MarksEditor.vue'
import RuleEditor from '../components/RuleEditor.vue'
import SettingsEditor from '../components/SettingsEditor.vue'
import ToggleSwitch from '../components/ToggleSwitch.vue'

const props = defineProps({ slug: { type: String, default: null } })
const router = useRouter()

const meta = ref(null)
const error = ref('')
const saving = ref(false)
const section = ref('general')

// The first question: jury-controlled or self-assessed. Everything that
// follows — tabs, rules, settings — depends on it, and the two flows
// never mix.
const modeChosen = ref(!!props.slug)

const form = reactive({
  name: '', slug: '', description: '', language: 'en', wiki_domain: '',
  start_date: '', end_date: '', scoring_mode: 'jury', status: null,
  settings: {}, rules: [], jury_usernames: [],
  suggested_articles: [], suggested_items: []
})
const juryText = ref('')
const suggestedArticlesText = ref('')
const suggestedItemsText = ref('')

const isJuryFlow = computed(() => form.scoring_mode === 'jury')
const isHybrid = computed({
  get: () => form.scoring_mode === 'hybrid',
  set: (v) => { form.scoring_mode = v ? 'hybrid' : 'self' }
})

const sections = computed(() => isJuryFlow.value
  ? [
      ['general', 'General'],
      ['eligibility', 'Eligibility'],
      ['marks', 'Marks'],
      ['jury', 'Jury'],
      ['display', 'Display']
    ]
  : [
      ['general', 'General'],
      ['rules', 'Point rules'],
      ['suggested', 'Suggested pages'],
      ['verification', 'Verification'],
      ['settings', 'Settings']
    ])

watch(sections, (list) => {
  if (!list.some(([key]) => key === section.value)) section.value = 'general'
})

function chooseMode (mode) {
  form.scoring_mode = mode
  modeChosen.value = true
  seedDefaults()
}

// Sensible starting points per flow, only for new campaigns.
function seedDefaults () {
  if (props.slug) return
  if (isJuryFlow.value) {
    if (!form.settings.jury_criteria?.length) {
      form.settings.jury_criteria = [{
        key: 'm1', title: 'Accept the article?', type: 'radio',
        values: [{ title: 'Yes', value: 1 }, { title: 'No', value: 0 }]
      }]
    }
  } else if (!form.rules.length && meta.value) {
    form.rules = meta.value.default_rules.self.map(r => ({ ...r }))
  }
}

onMounted(async () => {
  try {
    meta.value = (await api.meta()).data
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
  // Never mix the two campaign types: jury campaigns carry no point
  // rules, self-assessment campaigns carry no marks config.
  if (isJuryFlow.value) {
    payload.rules = []
    payload.suggested_items = []
  } else {
    payload.settings = { ...form.settings, jury_criteria: [] }
    if (!isHybrid.value) payload.jury_usernames = []
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
    <!-- ================= step 0: what kind of campaign? ================= -->
    <div v-if="!modeChosen" class="max-w-3xl mx-auto">
      <h1 class="text-2xl font-bold mb-1">Create a campaign</h1>
      <p class="text-sm text-neutral-500 dark:text-neutral-400 mb-6">
        First, the most important choice — how are contributions scored?
        This defines the whole setup of your campaign.
      </p>
      <div class="grid sm:grid-cols-2 gap-4">
        <button type="button"
                class="card p-6 text-left hover:border-blue-400 dark:hover:border-blue-600
                       focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                @click="chooseMode('jury')">
          <div class="text-3xl mb-3">⚖️</div>
          <div class="font-semibold text-lg mb-1">Jury assessment</div>
          <p class="text-sm text-neutral-600 dark:text-neutral-400">
            A jury reviews every submission with a marks form you design —
            radio groups, checkboxes and number scores. Points are the
            average of accepting reviews. Like Fountain.
          </p>
        </button>
        <button type="button"
                class="card p-6 text-left hover:border-blue-400 dark:hover:border-blue-600
                       focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                @click="chooseMode('self')">
          <div class="text-3xl mb-3">🖊️</div>
          <div class="font-semibold text-lg mb-1">Self-assessment</div>
          <p class="text-sm text-neutral-600 dark:text-neutral-400">
            Participants claim their own points under the campaign's point
            rules — bytes added, improvements, suggested pages, Wikidata
            statements. Organizers (or a verifying jury) check the claims
            and always have the final say.
          </p>
        </button>
      </div>
    </div>

    <!-- ======================= the config editor ======================== -->
    <template v-else>
      <div class="flex items-center gap-3 flex-wrap mb-1">
        <h1 class="text-2xl font-bold">{{ slug ? 'Edit campaign' : 'New campaign' }}</h1>
        <span class="badge"
              :class="isJuryFlow
                ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                : 'bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300'">
          {{ isJuryFlow ? 'Jury assessment' : (isHybrid ? 'Self-assessment + jury' : 'Self-assessment') }}
        </span>
        <button v-if="!slug" type="button" class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                @click="modeChosen = false">
          change type
        </button>
      </div>
      <p v-if="!slug" class="text-sm text-neutral-500 dark:text-neutral-400 mb-4">
        New campaigns start as drafts. They go live immediately if you hold
        admin (sysop) rights on the target wiki (jury) or on any Wikipedia
        project (self-assessment); otherwise a wiki admin must approve.
      </p>

      <div class="flex gap-1 border-b border-neutral-200 dark:border-neutral-800 mb-4 overflow-x-auto">
        <button v-for="[key, label] in sections" :key="key" type="button" class="tab"
                :class="{ 'tab-active': section === key }" @click="section = key">
          {{ label }}
        </button>
      </div>

      <form @submit.prevent="save">
        <!-- ============================ General ========================= -->
        <div v-show="section === 'general'" class="card p-4 grid gap-4 sm:grid-cols-2">
          <div class="sm:col-span-2">
            <label class="label">Name *</label>
            <input v-model="form.name" class="input" required minlength="3" />
          </div>
          <div>
            <label class="label">URL slug</label>
            <input v-model="form.slug" class="input" pattern="[a-z0-9][a-z0-9_-]*"
                   placeholder="auto-generated from name" />
            <p class="text-xs text-neutral-400 mt-1">
              wikistar.toolforge.org/campaigns/{{ form.slug || '…' }}
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label">Start date *</label>
              <input v-model="form.start_date" type="date" class="input" required />
            </div>
            <div>
              <label class="label">End date *</label>
              <input v-model="form.end_date" type="date" class="input" required />
            </div>
          </div>
          <div>
            <label class="label">Wiki language {{ !isJuryFlow && form.settings.multi_language ? '(default)' : '' }}</label>
            <LanguageSelect v-model="form.language" />
            <p v-if="!isJuryFlow" class="text-xs text-neutral-400 mt-1">
              Multi-language submissions can be enabled under Settings →
              Participation.
            </p>
          </div>
          <div>
            <label class="label">Wiki domain</label>
            <input v-model="form.wiki_domain" class="input"
                   :placeholder="`${form.language || 'en'}.wikipedia.org`" />
            <p class="text-xs text-neutral-400 mt-1">
              Leave empty for {{ form.language || 'en' }}.wikipedia.org.
            </p>
          </div>
          <div class="sm:col-span-2">
            <label class="label">Description</label>
            <textarea v-model="form.description" class="input" rows="4"
                      placeholder="Goals, rules and prizes of the campaign"></textarea>
          </div>
        </div>

        <!-- ====================== JURY FLOW ============================ -->
        <template v-if="isJuryFlow">
          <div v-show="section === 'eligibility'" class="space-y-4">
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['eligibility', 'participation']" />
            <div class="card p-4">
              <label class="label">Suggested articles (optional, one title per line)</label>
              <textarea v-model="suggestedArticlesText" class="input font-mono" rows="6"></textarea>
            </div>
          </div>

          <div v-show="section === 'marks'" class="space-y-4">
            <MarksEditor v-model="form.settings.jury_criteria" />
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['jury']" />
          </div>

          <div v-show="section === 'jury'" class="card p-4 max-w-xl">
            <label class="label">Jury members (one Wikimedia username per line)</label>
            <textarea v-model="juryText" class="input font-mono" rows="8"></textarea>
            <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
              Jurors review submissions with the marks form from the Marks
              tab. They are added to the campaign automatically and can be
              managed later from the campaign page.
            </p>
          </div>

          <div v-show="section === 'display'">
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['display']" />
          </div>
        </template>

        <!-- ================== SELF-ASSESSMENT FLOW ===================== -->
        <template v-else>
          <div v-show="section === 'rules'" class="space-y-4">
            <div class="card p-4 text-sm text-neutral-600 dark:text-neutral-400">
              Participants count their own points under these rules — e.g.
              <em>+1 point per 1,000 bytes added, +2 for a substantial
              improvement, +10 for a suggested article, +25 for a Good
              Article, Wikidata item/statement/label/reference points</em>.
              Rules marked <strong>auto</strong> are computed from the
              MediaWiki API; the others are claimed by participants and
              verified. The default set matches the classic contest rules
              and is fully editable.
            </div>
            <RuleEditor v-model="form.rules" :default-rules="meta.default_rules.self" />
          </div>

          <div v-show="section === 'suggested'" class="grid gap-4 md:grid-cols-2">
            <div class="card p-4">
              <label class="label">Suggested articles (one title per line)</label>
              <textarea v-model="suggestedArticlesText" class="input font-mono" rows="10"></textarea>
              <p class="text-xs text-neutral-500 mt-2">Submitting one earns the "suggested list" bonus rule.</p>
            </div>
            <div class="card p-4">
              <label class="label">Suggested Wikidata items (one QID per line)</label>
              <textarea v-model="suggestedItemsText" class="input font-mono" rows="10"></textarea>
            </div>
          </div>

          <div v-show="section === 'verification'" class="space-y-4">
            <div class="card p-4">
              <div class="flex items-center gap-4">
                <div class="flex-1">
                  <div class="text-sm font-medium">Dedicated verification jury</div>
                  <div class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                    Off: campaign organizers verify the participants' claims.
                    On (hybrid): a jury you name below verifies claims alongside
                    the organizers.
                  </div>
                </div>
                <ToggleSwitch v-model="isHybrid" />
              </div>
              <div v-if="isHybrid" class="mt-4">
                <label class="label">Verifying jury (one Wikimedia username per line)</label>
                <textarea v-model="juryText" class="input font-mono" rows="6"></textarea>
              </div>
            </div>
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['self_assessment']" />
          </div>

          <div v-show="section === 'settings'">
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['participation', 'eligibility', 'display']" />
          </div>
        </template>

        <p v-if="error" class="text-red-600 dark:text-red-400 text-sm mt-3">{{ error }}</p>
        <div class="mt-4 flex gap-2">
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving…' : (slug ? 'Save changes' : 'Create campaign') }}
          </button>
          <router-link class="btn" :to="slug ? `/campaigns/${slug}` : '/'">Cancel</router-link>
        </div>
      </form>
    </template>
  </div>
  <p v-else-if="error" class="text-red-600 dark:text-red-400">{{ error }}</p>
  <p v-else class="text-neutral-500">Loading…</p>
</template>
