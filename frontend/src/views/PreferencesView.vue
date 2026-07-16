<script setup>
import { onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'
import LanguageSelect from '../components/LanguageSelect.vue'
import { useAuthStore } from '../store'
import { useTheme } from '../theme'

const auth = useAuthStore()
const { theme, setTheme } = useTheme()

const languages = ref([])
const homeWikis = ref([])
const input = ref('')
const wikiInput = ref('')
const saving = ref(false)
const saved = ref(false)
const error = ref('')

// theme.js calls the follow-the-OS mode "system"; shown here as "Auto".
const themeChoices = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'Auto' }
]

onMounted(async () => {
  if (!auth.isLoggedIn && !auth.loaded) await auth.fetchUser()
  if (!auth.isLoggedIn) return
  try {
    const prefs = (await api.getPreferences()).data
    languages.value = prefs.preferred_languages
    homeWikis.value = prefs.home_wikis || []
  } catch (e) { error.value = errorMessage(e) }
})

function add () {
  const code = input.value
  if (!code) return
  error.value = ''
  if (!languages.value.includes(code) && languages.value.length < 10) {
    languages.value.push(code)
  }
  input.value = ''
}

function remove (code) {
  languages.value = languages.value.filter(l => l !== code)
}

function clearAll () {
  languages.value = []
  input.value = ''
}

function addWiki () {
  const code = wikiInput.value
  if (!code) return
  error.value = ''
  if (!homeWikis.value.includes(code) && homeWikis.value.length < 10) {
    homeWikis.value.push(code)
  }
  wikiInput.value = ''
}

function removeWiki (code) {
  homeWikis.value = homeWikis.value.filter(l => l !== code)
}

function clearWikis () {
  homeWikis.value = []
  wikiInput.value = ''
}

function move (i, d) {
  const j = i + d
  if (j < 0 || j >= languages.value.length) return
  const copy = [...languages.value]
  ;[copy[i], copy[j]] = [copy[j], copy[i]]
  languages.value = copy
}

async function save () {
  saving.value = true
  saved.value = false
  error.value = ''
  try {
    const prefs = (await api.savePreferences({
      preferred_languages: languages.value,
      home_wikis: homeWikis.value
    })).data
    languages.value = prefs.preferred_languages
    homeWikis.value = prefs.home_wikis || []
    saved.value = true
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl space-y-6">
    <h1 class="text-2xl font-bold">Preferences</h1>

    <p v-if="auth.loaded && !auth.isLoggedIn" class="text-neutral-600 dark:text-neutral-300">
      Please <a class="text-blue-600 dark:text-blue-400 hover:underline"
                :href="api.loginUrl">log in</a> to edit your preferences.
    </p>

    <template v-else>
      <!-- preferred languages -->
      <div class="card overflow-hidden">
        <header class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-800
                       bg-neutral-50 dark:bg-neutral-950/40">
          <h2 class="font-semibold text-sm">Preferred languages</h2>
          <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
            Suggested articles in campaigns are shown in these languages,
            in this order.
          </p>
        </header>
        <div class="p-4 space-y-3">
          <div v-if="languages.length" class="flex flex-wrap gap-1.5">
            <span v-for="(code, i) in languages" :key="code"
                  class="badge bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-300 gap-1">
              <button type="button" class="opacity-60 hover:opacity-100" title="Move left"
                      :disabled="i === 0" @click="move(i, -1)">‹</button>
              {{ code }}
              <button type="button" class="opacity-60 hover:opacity-100" title="Move right"
                      :disabled="i === languages.length - 1" @click="move(i, 1)">›</button>
              <button type="button" class="opacity-60 hover:opacity-100 ml-0.5" title="Remove"
                      @click="remove(code)">✕</button>
            </span>
          </div>
          <p v-else class="text-sm text-neutral-600 dark:text-neutral-300">
            No languages yet — campaign pages will fall back to the campaign's own language.
          </p>
          <form class="flex flex-wrap gap-2" @submit.prevent="add">
            <LanguageSelect v-model="input" class="!w-64"
                            placeholder="Add a language…" />
            <button class="btn" :disabled="!input || languages.length >= 10">Add</button>
            <button type="button" class="btn" :disabled="!languages.length && !input"
                    @click="clearAll">Clear</button>
          </form>
        </div>
      </div>

      <!-- home wikis -->
      <div class="card overflow-hidden">
        <header class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-800
                       bg-neutral-50 dark:bg-neutral-950/40">
          <h2 class="font-semibold text-sm">Home wikis</h2>
          <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
            The Wikipedias you mainly edit — search and add one or more
            projects, e.g. ml.wikipedia.org.
          </p>
        </header>
        <div class="p-4 space-y-3">
          <div v-if="homeWikis.length" class="flex flex-wrap gap-1.5">
            <span v-for="code in homeWikis" :key="code"
                  class="badge bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-300 gap-1">
              {{ code }}.wikipedia.org
              <button type="button" class="opacity-60 hover:opacity-100 ml-0.5" title="Remove"
                      @click="removeWiki(code)">✕</button>
            </span>
          </div>
          <p v-else class="text-sm text-neutral-600 dark:text-neutral-300">
            No home wiki yet.
          </p>
          <form class="flex flex-wrap gap-2" @submit.prevent="addWiki">
            <LanguageSelect v-model="wikiInput" wiki class="!w-72"
                            placeholder="Search a Wikipedia…" />
            <button class="btn" :disabled="!wikiInput || homeWikis.length >= 10">Add</button>
            <button type="button" class="btn" :disabled="!homeWikis.length && !wikiInput"
                    @click="clearWikis">Clear</button>
          </form>
        </div>
      </div>

      <!-- theme (stored on this device) -->
      <div class="card overflow-hidden">
        <header class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-800
                       bg-neutral-50 dark:bg-neutral-950/40">
          <h2 class="font-semibold text-sm">Theme</h2>
          <p class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
            Applied immediately and remembered on this device. Auto follows
            your system setting.
          </p>
        </header>
        <div class="p-4 flex gap-2">
          <button v-for="c in themeChoices" :key="c.value" type="button"
                  class="btn" :class="theme === c.value && '!bg-blue-600 !border-blue-600 !text-white'"
                  @click="setTheme(c.value)">
            {{ c.label }}
          </button>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button type="button" class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? 'Saving…' : 'Save preferences' }}
        </button>
        <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
        <p v-else-if="saved" class="text-sm text-green-700 dark:text-green-400">Preferences saved.</p>
      </div>
    </template>
  </div>
</template>
