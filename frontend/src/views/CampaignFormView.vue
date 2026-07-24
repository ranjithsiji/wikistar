<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { CdxDialog, CdxTextInput, CdxTextArea } from '@wikimedia/codex'
import api, { errorMessage } from '../api'
import AppMessage from '../components/AppMessage.vue'
import LanguageSelect from '../components/LanguageSelect.vue'
import MarksEditor from '../components/MarksEditor.vue'
import RuleEditor from '../components/RuleEditor.vue'
import SettingsEditor from '../components/SettingsEditor.vue'
import ToggleSwitch from '../components/ToggleSwitch.vue'
import UserPicker from '../components/UserPicker.vue'

const props = defineProps({ slug: { type: String, default: null } })
const router = useRouter()

const meta = ref(null)
const error = ref('')
const notice = ref('')
const saving = ref(false)
const section = ref('general')
const formEl = ref(null)

// Creation is a wizard: every Next saves the campaign (created as a
// draft on the first step), the last step activates it. `createdSlug`
// tracks the draft once it exists.
const createdSlug = ref(props.slug)
const isWizard = computed(() => !props.slug)
const canActivate = ref(false)

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
const juryUsers = ref([])
const coordinatorUsers = ref([])
const suggestedArticlesText = ref('')
// Suggested Wikidata items grouped under headings: each block is one
// section (empty heading = the default group).
const itemSections = ref([{ heading: '', text: '' }])

const juryWiki = computed(() =>
  form.wiki_domain || `${form.language || 'en'}.wikipedia.org`)

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

const stepIndex = computed(() =>
  sections.value.findIndex(([key]) => key === section.value))
const isLastStep = computed(() =>
  stepIndex.value === sections.value.length - 1)
const maxVisited = ref(0)
watch(stepIndex, (i) => { maxVisited.value = Math.max(maxVisited.value, i) })

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
  } else {
    if (!form.rules.length && meta.value) {
      form.rules = meta.value.default_rules.self.map(r => ({ ...r }))
    }
    // Self-assessment campaigns span multiple projects by default.
    form.settings.multi_language = true
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
      juryUsers.value = c.members.filter(m => m.role === 'jury')
        .map(m => m.user.username)
      coordinatorUsers.value = c.members.filter(m => m.role === 'organizer')
        .map(m => m.user.username)
      suggestedArticlesText.value = c.suggested_articles.join('\n')
      itemSections.value = itemsToSections(c.suggested_items)
    }
  } catch (e) {
    error.value = errorMessage(e)
  }
})

function splitLines (text) {
  return text.split('\n').map(s => s.trim()).filter(Boolean)
}

// Group the flat {qid, section} list from the API into editor blocks,
// preserving heading order (empty-heading group first).
function itemsToSections (items) {
  const order = []
  const byHeading = new Map()
  for (const it of items) {
    const h = it.section || ''
    if (!byHeading.has(h)) { byHeading.set(h, []); order.push(h) }
    byHeading.get(h).push(it.qid)
  }
  const blocks = order.map(h => ({ heading: h, text: byHeading.get(h).join('\n') }))
  return blocks.length ? blocks : [{ heading: '', text: '' }]
}

// Flatten the editor blocks back to a {qid, section} list for the API.
function sectionsToItems () {
  const out = []
  for (const block of itemSections.value) {
    for (const qid of splitLines(block.text)) {
      out.push({ qid, section: block.heading.trim() })
    }
  }
  return out
}

// The suggested step: Wikipedia / Wikidata top tabs, heading sets as
// sub-tabs; new sets are added through a small dialog.
const suggestedTab = ref('wikidata')
const activeSetIndex = ref(0)
const activeSet = computed(() => itemSections.value[activeSetIndex.value])
const totalSuggestedItems = computed(() =>
  itemSections.value.reduce((n, b) => n + splitLines(b.text).length, 0))

// Adding a set is one self-contained popup: heading + its QIDs together,
// rather than creating an empty set and hunting for the textarea below.
const showAddSet = ref(false)
const newSetName = ref('')
const newSetText = ref('')
function openAddSet () {
  newSetName.value = ''
  newSetText.value = ''
  showAddSet.value = true
}
function confirmAddSet () {
  itemSections.value.push({ heading: newSetName.value.trim(), text: newSetText.value })
  activeSetIndex.value = itemSections.value.length - 1
  showAddSet.value = false
}
function removeSet (i) {
  itemSections.value.splice(i, 1)
  if (!itemSections.value.length) itemSections.value.push({ heading: '', text: '' })
  activeSetIndex.value = Math.min(activeSetIndex.value,
                                  itemSections.value.length - 1)
}

function buildPayload () {
  const payload = {
    ...form,
    slug: form.slug || null,
    wiki_domain: form.wiki_domain || null,
    jury_usernames: [...juryUsers.value],
    coordinator_usernames: [...coordinatorUsers.value],
    suggested_articles: splitLines(suggestedArticlesText.value),
    suggested_items: sectionsToItems()
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
  return payload
}

// Create the draft on the first Next, update it afterwards.
async function persist () {
  const payload = buildPayload()
  const { data } = createdSlug.value
    ? await api.updateCampaign(createdSlug.value, payload)
    : await api.createCampaign(payload)
  if (!createdSlug.value) {
    createdSlug.value = data.slug
    form.slug = data.slug
    canActivate.value = data.status === 'draft'
      ? (await api.approvalRights(data.slug)).data.can_approve
      : false
  }
  form.status = data.status
  form.rules = data.rules.map(r => ({ ...r }))
  return data
}

// HTML5-validate only the controls of the visible step.
function validateVisible () {
  for (const el of formEl.value.querySelectorAll('input, select, textarea')) {
    if (el.offsetParent === null) continue
    if (!el.reportValidity()) return false
  }
  return true
}

async function nextStep () {
  if (!validateVisible()) return
  saving.value = true
  error.value = ''
  notice.value = ''
  try {
    const data = await persist()
    if (isLastStep.value) {
      if (data.status === 'draft' && canActivate.value) {
        await api.approveCampaign(createdSlug.value)
      }
      router.push(`/campaigns/${createdSlug.value}`)
    } else {
      notice.value = 'Draft saved.'
      section.value = sections.value[stepIndex.value + 1][0]
    }
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    saving.value = false
  }
}

function backStep () {
  if (stepIndex.value > 0) {
    section.value = sections.value[stepIndex.value - 1][0]
  }
}

const finishLabel = computed(() => {
  if (form.status === 'active') return 'Finish'
  return canActivate.value ? 'Activate campaign' : 'Finish — awaits approval'
})

// Edit mode: single save button, no wizard.
async function save () {
  if (isWizard.value) return nextStep()
  saving.value = true
  error.value = ''
  try {
    await persist()
    router.push(`/campaigns/${createdSlug.value}`)
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
      <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-6">
        First, the most important choice — how are contributions scored?
        This defines the whole setup of your campaign.
      </p>
      <div class="grid sm:grid-cols-2 gap-4">
        <button type="button"
                class="card p-6 text-left hover:border-blue-400 dark:hover:border-blue-600
                       focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                @click="chooseMode('jury')">
          <div class="flex items-center gap-3 mb-3">
            <span class="text-3xl">⚖️</span>
            <span class="badge bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
              Single project
            </span>
          </div>
          <div class="font-semibold text-lg mb-1">Jury assessment</div>
          <p class="text-sm text-neutral-600 dark:text-neutral-400">
            Runs on one wiki. A jury reviews every submission with a marks
            form you design — radio groups, checkboxes and number scores.
            Points are the average of accepting reviews. Like Fountain.
          </p>
        </button>
        <button type="button"
                class="card p-6 text-left hover:border-blue-400 dark:hover:border-blue-600
                       focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                @click="chooseMode('self')">
          <div class="flex items-center gap-3 mb-3">
            <span class="text-3xl">🖊️</span>
            <span class="badge bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300">
              Multiple projects
            </span>
          </div>
          <div class="font-semibold text-lg mb-1">Self-assessment</div>
          <p class="text-sm text-neutral-600 dark:text-neutral-400">
            Participants contribute across language Wikipedias and Wikidata,
            claiming their own points under the campaign's point rules —
            bytes added, improvements, suggested pages, statements.
            Coordinators verify the claims before the winners are announced
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
        <button v-if="!createdSlug" type="button" class="text-xs text-link-700 dark:text-link-400 hover:underline"
                @click="modeChosen = false">
          change type
        </button>
        <span v-if="isWizard" class="text-xs text-neutral-500 dark:text-neutral-400">
          Step {{ stepIndex + 1 }} of {{ sections.length }}
        </span>
      </div>
      <p v-if="!slug" class="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
        New campaigns start as drafts. They go live immediately if you hold
        admin (sysop) rights on the target wiki (jury) or on any Wikipedia
        project (self-assessment); otherwise a wiki admin must approve.
      </p>

      <div class="tab-group mb-4 w-fit max-w-full overflow-x-auto">
        <button v-for="([key, label], i) in sections" :key="key" type="button" class="tab"
                :class="{ 'tab-active': section === key,
                          'opacity-40 !cursor-default': isWizard && i > maxVisited }"
                :disabled="isWizard && i > maxVisited"
                @click="section = key">
          <span v-if="isWizard"
                class="inline-flex items-center justify-center w-4.5 h-4.5 mr-1 rounded-full text-[10px] font-bold"
                :class="i < stepIndex ? 'bg-green-600 text-white'
                  : section === key ? 'bg-blue-600 text-white'
                  : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300'">
            {{ i < stepIndex ? '✓' : i + 1 }}
          </span>
          {{ label }}
        </button>
      </div>

      <form ref="formEl" @submit.prevent="save">
        <!-- ============================ General ========================= -->
        <div v-show="section === 'general'" class="card p-4 grid gap-4 sm:grid-cols-2">
          <div class="sm:col-span-2">
            <label class="label">Name *</label>
            <cdx-text-input v-model="form.name" required minlength="3" />
          </div>
          <div>
            <label class="label">URL slug</label>
            <cdx-text-input v-model="form.slug" pattern="[a-z0-9][a-z0-9_-]*"
                            placeholder="auto-generated from name" />
            <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              wikistar.toolforge.org/campaigns/{{ form.slug || '…' }}
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label">Start date *</label>
              <cdx-text-input v-model="form.start_date" input-type="date" required />
            </div>
            <div>
              <label class="label">End date *</label>
              <cdx-text-input v-model="form.end_date" input-type="date" required />
            </div>
          </div>
          <div>
            <label class="label">Wiki language {{ !isJuryFlow && form.settings.multi_language ? '(default)' : '' }}</label>
            <LanguageSelect v-model="form.language" />
            <p v-if="!isJuryFlow" class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              Multi-language submissions can be enabled under Settings →
              Participation.
            </p>
          </div>
          <div>
            <label class="label">Wiki domain</label>
            <cdx-text-input v-model="form.wiki_domain"
                            :placeholder="`${form.language || 'en'}.wikipedia.org`" />
            <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              Leave empty for {{ form.language || 'en' }}.wikipedia.org.
            </p>
          </div>
          <div class="sm:col-span-2">
            <label class="label">Description</label>
            <cdx-text-area v-model="form.description" :rows="4"
                           placeholder="Goals, rules and prizes of the campaign" />
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

          <div v-show="section === 'jury'" class="space-y-4 max-w-2xl">
            <div class="card p-4">
              <label class="label">Jury members</label>
              <UserPicker v-model="juryUsers" :wiki="juryWiki" />
              <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-3">
                Start typing to search Wikimedia accounts, then press Enter or
                Add. Jurors review submissions with the marks form from the
                Marks tab; they can be managed later from the campaign page.
              </p>
            </div>
            <div class="card p-4">
              <label class="label">Coordinators</label>
              <UserPicker v-model="coordinatorUsers" :wiki="juryWiki" />
              <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-3">
                Coordinators (organizers) manage the campaign, moderate
                submissions and have the final say. The campaign creator is
                always a coordinator.
              </p>
            </div>
          </div>

          <div v-show="section === 'display'">
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['template', 'display']" />
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

          <div v-show="section === 'suggested'" class="card">
            <!-- Wikidata / Wikipedia top tabs -->
            <div class="tab-group m-3">
              <button type="button" class="tab"
                      :class="{ 'tab-active': suggestedTab === 'wikidata' }"
                      @click="suggestedTab = 'wikidata'">
                Wikidata items
                <span class="text-xs text-neutral-400 dark:text-neutral-500">
                  ({{ totalSuggestedItems }})</span>
              </button>
              <button type="button" class="tab"
                      :class="{ 'tab-active': suggestedTab === 'wikipedia' }"
                      @click="suggestedTab = 'wikipedia'">
                Wikipedia articles
                <span class="text-xs text-neutral-400 dark:text-neutral-500">
                  ({{ splitLines(suggestedArticlesText).length }})</span>
              </button>
            </div>

            <!-- Wikidata items: one label button per heading set -->
            <div v-show="suggestedTab === 'wikidata'" class="p-4">
              <p class="text-xs text-neutral-600 dark:text-neutral-300 mb-3">
                Group items under headings (e.g. "Districts", "Rivers"); each
                heading becomes a tab on the campaign page. One QID per line.
              </p>
              <div class="flex flex-wrap items-center gap-2 mb-2">
                <button v-for="(block, i) in itemSections" :key="i" type="button"
                        class="rounded-full border px-3 py-1 text-sm font-medium transition-colors"
                        :class="activeSetIndex === i
                          ? 'bg-blue-700 border-blue-700 text-white'
                          : 'border-neutral-300 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800'"
                        @click="activeSetIndex = i">
                  {{ block.heading || 'General' }}
                  <span :class="activeSetIndex === i
                          ? 'text-blue-100' : 'text-neutral-400 dark:text-neutral-500'"
                        class="text-xs">({{ splitLines(block.text).length }})</span>
                </button>
              </div>
              <!-- add-set button on its own line -->
              <div class="mb-4">
                <button type="button" class="btn text-sm" @click="openAddSet">
                  + New set
                </button>
              </div>
              <div v-if="activeSet">
                <div class="flex flex-wrap items-end gap-3 mb-3">
                  <div>
                    <label class="label">Heading</label>
                    <cdx-text-input v-model="activeSet.heading" class="!w-72"
                                    placeholder='Empty shows as "General"' />
                  </div>
                  <span class="flex-1"></span>
                  <button type="button" class="btn-danger !py-1.5 text-xs"
                          @click="removeSet(activeSetIndex)">Remove this set</button>
                </div>
                <label class="label">QIDs (one per line)</label>
                <textarea v-model="activeSet.text" class="input font-mono" rows="12"
                          placeholder="Q42&#10;Q123"></textarea>
              </div>
            </div>

            <!-- Wikipedia articles -->
            <div v-show="suggestedTab === 'wikipedia'" class="p-4">
              <label class="label">Suggested articles (one title per line)</label>
              <textarea v-model="suggestedArticlesText" class="input font-mono" rows="14"></textarea>
              <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-2">
                Submitting one earns the "suggested list" bonus rule.
              </p>
            </div>
          </div>

          <div v-show="section === 'verification'" class="space-y-4">
            <div class="card p-4">
              <label class="label">Coordinators</label>
              <UserPicker v-model="coordinatorUsers" :wiki="juryWiki" />
              <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-3">
                Coordinators (organizers) verify the participants' claims,
                moderate submissions and announce the winners. The campaign
                creator is always a coordinator.
              </p>
            </div>
            <div class="card p-4">
              <div class="flex items-center gap-4">
                <div class="flex-1">
                  <div class="text-sm font-medium">Dedicated verification jury</div>
                  <div class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
                    Off: campaign organizers verify the participants' claims.
                    On (hybrid): a jury you name below verifies claims alongside
                    the organizers.
                  </div>
                </div>
                <ToggleSwitch v-model="isHybrid" />
              </div>
              <div v-if="isHybrid" class="mt-4">
                <label class="label">Verifying jury</label>
                <UserPicker v-model="juryUsers" :wiki="juryWiki" />
              </div>
            </div>
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['self_assessment']" />
          </div>

          <div v-show="section === 'settings'">
            <SettingsEditor v-model="form.settings" :registry="meta.settings_registry"
                            :categories="['participation', 'eligibility', 'template', 'display']" />
          </div>
        </template>

        <AppMessage v-model="error" type="error" class="mt-3" />
        <AppMessage v-if="!error" v-model="notice" type="success" class="mt-3" />

        <!-- wizard footer: every Next saves; the last step activates -->
        <div v-if="isWizard" class="mt-4 flex items-center gap-2">
          <button type="button" class="btn" :disabled="stepIndex === 0 || saving"
                  @click="backStep">← Back</button>
          <span class="flex-1"></span>
          <router-link class="btn" :to="createdSlug ? `/campaigns/${createdSlug}` : '/'">
            {{ createdSlug ? 'Finish later' : 'Cancel' }}
          </router-link>
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving…'
              : isLastStep ? finishLabel
              : (createdSlug ? 'Save & Next →' : 'Create draft & Next →') }}
          </button>
        </div>
        <!-- edit mode: plain save -->
        <div v-else class="mt-4 flex gap-2">
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save changes' }}
          </button>
          <router-link class="btn" :to="`/campaigns/${slug}`">Cancel</router-link>
        </div>
      </form>

      <!-- new heading-set popup: title + its QIDs together, one self-
           contained action instead of creating an empty set to fill in
           below (teleports to body, entirely outside the campaign form) -->
      <cdx-dialog v-model:open="showAddSet" title="New heading set"
                  :use-close-button="true"
                  :primary-action="{ label: 'Add set', actionType: 'progressive' }"
                  :default-action="{ label: 'Cancel' }"
                  @primary="confirmAddSet" @default="showAddSet = false">
        <label class="label">Heading</label>
        <cdx-text-input v-model="newSetName" class="mb-3"
                        placeholder='e.g. "Districts", "Rivers"' />
        <label class="label">QIDs (one per line)</label>
        <textarea v-model="newSetText" class="input font-mono" rows="8"
                  placeholder="Q42&#10;Q123 (new set)"></textarea>
        <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-2">
          The heading becomes a tab on the campaign page. Leave it empty
          for the unlabelled "General" group.
        </p>
      </cdx-dialog>
    </template>
  </div>
  <AppMessage v-else-if="error" v-model="error" type="error" />
  <p v-else class="text-neutral-600 dark:text-neutral-300">Loading…</p>
</template>
