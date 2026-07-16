<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

// Page-title input with live suggestions from the target wiki
// (prefixsearch; wbsearchentities for Wikidata items). v-model is the
// raw title — typing, pasting and picking a suggestion all update it.
const model = defineModel({ type: String, default: '' })
const props = defineProps({
  wiki: { type: String, required: true },       // target wiki domain
  kind: { type: String, default: 'article' },   // article | wikidata_item | commons_file
  placeholder: { type: String, default: '' },
  required: { type: Boolean, default: false }
})

const suggestions = ref([])   // [{title, description?}]
const open = ref(false)
const active = ref(0)
const root = ref(null)
let timer = null
let controller = null

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
})

function onInput (e) {
  model.value = e.target.value
  clearTimeout(timer)
  timer = setTimeout(fetchSuggestions, 250)
}

function pick (s) {
  model.value = s.title
  suggestions.value = []
  open.value = false
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
onBeforeUnmount(() => { document.removeEventListener('click', onDocumentClick); clearTimeout(timer) })
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
  </div>
</template>
