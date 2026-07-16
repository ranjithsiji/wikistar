<script setup>
import { onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../store'

const auth = useAuthStore()
const languages = ref([])
const input = ref('')
const saving = ref(false)
const saved = ref(false)
const error = ref('')

onMounted(async () => {
  if (!auth.isLoggedIn && !auth.loaded) await auth.fetchUser()
  if (!auth.isLoggedIn) return
  try {
    languages.value = (await api.getPreferences()).data.preferred_languages
  } catch (e) { error.value = errorMessage(e) }
})

function add () {
  const code = input.value.trim().toLowerCase()
  if (!code) return
  if (!/^[a-z][a-z0-9-]{1,11}$/.test(code)) {
    error.value = `"${code}" does not look like a wiki language code`
    return
  }
  error.value = ''
  if (!languages.value.includes(code) && languages.value.length < 10) {
    languages.value.push(code)
  }
  input.value = ''
}

function remove (code) {
  languages.value = languages.value.filter(l => l !== code)
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
    languages.value = (await api.savePreferences({
      preferred_languages: languages.value
    })).data.preferred_languages
    saved.value = true
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl">
    <h1 class="text-2xl font-bold mb-4">Preferences</h1>

    <p v-if="auth.loaded && !auth.isLoggedIn" class="text-neutral-500 dark:text-neutral-400">
      Please <a class="text-blue-600 dark:text-blue-400 hover:underline"
                :href="api.loginUrl">log in</a> to edit your preferences.
    </p>

    <div v-else class="card overflow-hidden">
      <header class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-800
                     bg-neutral-50 dark:bg-neutral-950/40">
        <h2 class="font-semibold text-sm">Preferred languages</h2>
        <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          Suggested Wikidata items in campaigns show wikilinks in these
          languages, in this order. Use wiki language codes such as
          <code>ml</code>, <code>ta</code>, <code>hi</code>, <code>en</code>.
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
        <p v-else class="text-sm text-neutral-500 dark:text-neutral-400">
          No languages yet — campaign pages will fall back to the campaign's own language.
        </p>
        <form class="flex gap-2" @submit.prevent="add">
          <input v-model="input" class="input !w-40" placeholder="e.g. ml"
                 maxlength="12" :disabled="languages.length >= 10" />
          <button class="btn" :disabled="!input.trim() || languages.length >= 10">Add</button>
          <span class="flex-1"></span>
          <button type="button" class="btn-primary" :disabled="saving" @click="save">
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
        </form>
        <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
        <p v-else-if="saved" class="text-sm text-green-700 dark:text-green-400">Preferences saved.</p>
      </div>
    </div>
  </div>
</template>
