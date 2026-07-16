<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

// Multi-user picker with autocomplete against the global Wikimedia
// account list (CentralAuth, meta.wikimedia.org globalallusers).
// v-model: array of usernames. Each picked user renders as a chip
// linking to their user page on `wiki`.
const users = defineModel({ type: Array, required: true })
const props = defineProps({
  wiki: { type: String, default: 'meta.wikimedia.org' },
  placeholder: { type: String, default: 'Type a Wikimedia username…' }
})

const query = ref('')
const suggestions = ref([])
const open = ref(false)
const active = ref(0)
const root = ref(null)
let timer = null
let controller = null

function userUrl (name) {
  return `https://${props.wiki}/wiki/User:${encodeURIComponent(name.replaceAll(' ', '_'))}`
}

async function fetchSuggestions () {
  const raw = query.value.trim()
  if (raw.length < 2) { suggestions.value = []; open.value = false; return }
  // MediaWiki usernames start uppercase; the prefix match is case-sensitive.
  const prefix = raw[0].toUpperCase() + raw.slice(1)
  controller?.abort()
  controller = new AbortController()
  try {
    const url = 'https://meta.wikimedia.org/w/api.php?action=query&list=globalallusers'
      + `&aguprefix=${encodeURIComponent(prefix)}&agulimit=8&format=json&origin=*`
    const data = await (await fetch(url, { signal: controller.signal })).json()
    suggestions.value = (data.query?.globalallusers || [])
      .map(u => u.name)
      .filter(name => !users.value.includes(name))
    active.value = 0
    open.value = true
  } catch { /* aborted or offline — keep whatever we had */ }
}

function onInput (e) {
  query.value = e.target.value
  clearTimeout(timer)
  timer = setTimeout(fetchSuggestions, 250)
}

function add (name) {
  name = (name || '').trim()
  if (!name) return
  name = name[0].toUpperCase() + name.slice(1)
  if (!users.value.includes(name)) users.value.push(name)
  query.value = ''
  suggestions.value = []
  open.value = false
}

function remove (name) {
  users.value = users.value.filter(u => u !== name)
}

function onKeydown (e) {
  if (e.key === 'ArrowDown' && open.value) {
    e.preventDefault()
    active.value = Math.min(active.value + 1, suggestions.value.length - 1)
  } else if (e.key === 'ArrowUp' && open.value) {
    e.preventDefault()
    active.value = Math.max(active.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    add(open.value && suggestions.value[active.value]
      ? suggestions.value[active.value] : query.value)
  } else if (e.key === 'Escape') {
    open.value = false
  }
}

function onDocumentClick (e) {
  if (root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>

<template>
  <div ref="root">
    <div v-if="users.length" class="flex flex-wrap gap-1.5 mb-2">
      <span v-for="name in users" :key="name"
            class="badge bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-300 gap-1.5">
        <a :href="userUrl(name)" target="_blank" rel="noopener" class="hover:underline">
          {{ name }}
        </a>
        <button type="button" class="opacity-60 hover:opacity-100" title="Remove"
                @click="remove(name)">✕</button>
      </span>
    </div>
    <div class="relative max-w-md">
      <div class="flex gap-2">
        <input class="input" :value="query" :placeholder="placeholder"
               autocomplete="off" @input="onInput" @keydown="onKeydown"
               @focus="suggestions.length && (open = true)" />
        <button type="button" class="btn" :disabled="!query.trim()" @click="add(query)">
          Add
        </button>
      </div>
      <div v-if="open && suggestions.length"
           class="absolute z-30 mt-1 w-full max-h-56 overflow-y-auto card shadow-lg py-1">
        <button v-for="(name, i) in suggestions" :key="name" type="button"
                class="block w-full text-left px-3 py-1.5 text-sm"
                :class="i === active && 'bg-neutral-100 dark:bg-neutral-800'"
                @mouseenter="active = i" @click="add(name)">
          {{ name }}
        </button>
      </div>
    </div>
  </div>
</template>
