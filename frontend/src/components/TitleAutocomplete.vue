<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

// Page-title input with live suggestions from the target wiki
// (prefixsearch; wbsearchentities for Wikidata items). v-model is the
// raw title — typing, pasting and picking a suggestion all update it.
// Also fires a debounced existence check against the same wiki, so a
// title that doesn't exist there (e.g. picked for the wrong project in
// a multi-language campaign) surfaces a warning before the user submits
// — this is a fast, client-side hint only; the server still verifies
// and is the real gate.
const model = defineModel({ type: String, default: '' })
const props = defineProps({
  wiki: { type: String, required: true },       // target wiki domain
  kind: { type: String, default: 'article' },   // article | wikidata_item | commons_file
  placeholder: { type: String, default: '' },
  required: { type: Boolean, default: false }
})
const emit = defineEmits(['update:exists'])

const suggestions = ref([])   // [{title, description?}]
const open = ref(false)
const active = ref(0)
const root = ref(null)
let timer = null
let controller = null

// null = unknown/not checked yet, true/false = confirmed.
const exists = ref(null)
let existsController = null
async function checkExists () {
  const title = model.value.trim()
  existsController?.abort()
  if (!title) { exists.value = null; emit('update:exists', null); return }
  existsController = new AbortController()
  try {
    let url
    if (props.kind === 'wikidata_item') {
      url = 'https://www.wikidata.org/w/api.php?action=wbgetentities'
        + `&ids=${encodeURIComponent(title.toUpperCase())}&props=info&format=json&origin=*`
    } else {
      url = `https://${props.wiki}/w/api.php?action=query`
        + `&titles=${encodeURIComponent(title)}&format=json&origin=*`
    }
    const data = await (await fetch(url, { signal: existsController.signal })).json()
    const found = props.kind === 'wikidata_item'
      ? !(data.entities?.[title.toUpperCase()]?.missing !== undefined)
      : !Object.values(data.query?.pages || {}).some(p => p.missing !== undefined)
    exists.value = found
    emit('update:exists', found)
  } catch { /* aborted or offline — stay unknown, don't block the user */ }
}

async function fetchSuggestions () {
  const q = model.value.trim()
  if (q.length < 2) { suggestions.value = []; open.value = false; return }
  controller?.abort()
  controller = new AbortController()
  try {
    let url
    if (props.kind === 'wikidata_item') {
      url = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&type=item'
        + `&search=${encodeURIComponent(q)}&language=en&uselang=en&limit=8&format=json&origin=*`
    } else {
      const ns = props.kind === 'commons_file' ? 6 : 0
      url = `https://${props.wiki}/w/api.php?action=query&list=prefixsearch`
        + `&pssearch=${encodeURIComponent(q)}&psnamespace=${ns}&pslimit=8&format=json&origin=*`
    }
    const data = await (await fetch(url, { signal: controller.signal })).json()
    suggestions.value = props.kind === 'wikidata_item'
      ? (data.search || []).map(e => ({ title: e.id, description: e.label }))
      : (data.query?.prefixsearch || []).map(p => ({ title: p.title }))
    active.value = 0
    open.value = suggestions.value.length > 0
  } catch { /* aborted or offline — keep whatever we had */ }
}

watch(() => [props.wiki, props.kind], () => {
  suggestions.value = []
  open.value = false
  exists.value = null
  emit('update:exists', null)
  if (model.value.trim()) checkExists()
})

let existsTimer = null
function onInput (e) {
  model.value = e.target.value
  exists.value = null
  emit('update:exists', null)
  clearTimeout(timer)
  clearTimeout(existsTimer)
  timer = setTimeout(fetchSuggestions, 250)
  existsTimer = setTimeout(checkExists, 400)
}

function pick (s) {
  model.value = s.title
  suggestions.value = []
  open.value = false
  // Picked straight from suggestions pulled from this same wiki — no
  // need for a separate existence round-trip.
  exists.value = true
  emit('update:exists', true)
}

function onKeydown (e) {
  if (!open.value) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    active.value = Math.min(active.value + 1, suggestions.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    active.value = Math.max(active.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (suggestions.value[active.value]) pick(suggestions.value[active.value])
  } else if (e.key === 'Escape') {
    open.value = false
  }
}

function onDocumentClick (e) {
  if (root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  clearTimeout(timer)
  clearTimeout(existsTimer)
})
</script>

<template>
  <div ref="root" class="relative">
    <input class="input" role="combobox" :aria-expanded="open"
           :value="model" :placeholder="placeholder" :required="required"
           autocomplete="off" @input="onInput" @keydown="onKeydown"
           @focus="suggestions.length && (open = true)" />
    <div v-if="open" class="absolute z-30 mt-1 w-full max-h-64 overflow-y-auto card shadow-lg py-1">
      <button v-for="(s, i) in suggestions" :key="s.title" type="button"
              class="block w-full text-left px-3 py-1.5 text-sm"
              :class="i === active && 'bg-neutral-100 dark:bg-neutral-800'"
              @mouseenter="active = i" @click="pick(s)">
        {{ s.title }}
        <span v-if="s.description" class="text-neutral-500 dark:text-neutral-400">
          — {{ s.description }}</span>
      </button>
    </div>
    <p v-if="exists === false" class="text-xs text-red-600 dark:text-red-400 mt-1">
      {{ kind === 'wikidata_item'
         ? `${model.trim()} was not found on Wikidata.`
         : `"${model.trim()}" was not found on ${wiki}. Check the project/title.` }}
    </p>
  </div>
</template>
