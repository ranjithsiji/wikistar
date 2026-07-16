<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// Single-user dropdown for the submit form. Opens with the campaign's
// participants; typing also searches the global Wikimedia account list
// (CentralAuth, like UserPicker). v-model is the chosen username.
const model = defineModel({ type: String, default: '' })
const props = defineProps({
  participants: { type: Array, default: () => [] },   // usernames offered first
  placeholder: { type: String, default: 'Select or search a user…' },
  required: { type: Boolean, default: false }
})

const globalMatches = ref([])
const open = ref(false)
const active = ref(0)
const root = ref(null)
let timer = null
let controller = null

const suggestions = computed(() => {
  const q = model.value.trim().toLowerCase()
  const local = props.participants
    .filter(name => !q || name.toLowerCase().includes(q))
  const seen = new Set(local)
  return [...local, ...globalMatches.value.filter(n => !seen.has(n))].slice(0, 12)
})

async function searchGlobal () {
  const raw = model.value.trim()
  if (raw.length < 2) { globalMatches.value = []; return }
  const prefix = raw[0].toUpperCase() + raw.slice(1)
  controller?.abort()
  controller = new AbortController()
  try {
    const url = 'https://meta.wikimedia.org/w/api.php?action=query&list=globalallusers'
      + `&aguprefix=${encodeURIComponent(prefix)}&agulimit=8&format=json&origin=*`
    const data = await (await fetch(url, { signal: controller.signal })).json()
    globalMatches.value = (data.query?.globalallusers || []).map(u => u.name)
    active.value = 0
  } catch { /* aborted or offline — keep whatever we had */ }
}

function onInput (e) {
  model.value = e.target.value
  open.value = true
  clearTimeout(timer)
  timer = setTimeout(searchGlobal, 250)
}

function pick (name) {
  model.value = name
  open.value = false
}

function onKeydown (e) {
  if (!open.value && e.key === 'ArrowDown') {
    e.preventDefault()
    open.value = true
    return
  }
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
    else open.value = false
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
           @focus="open = true" @click="open = true" />
    <div v-if="open && suggestions.length"
         class="absolute z-30 mt-1 w-full max-h-56 overflow-y-auto card shadow-lg py-1">
      <button v-for="(name, i) in suggestions" :key="name" type="button"
              class="block w-full text-left px-3 py-1.5 text-sm"
              :class="[i === active && 'bg-neutral-100 dark:bg-neutral-800',
                       name === model && 'font-semibold text-blue-700 dark:text-blue-400']"
              @mouseenter="active = i" @click="pick(name)">
        {{ name }}
        <span v-if="participants.includes(name)"
              class="text-xs text-neutral-500 dark:text-neutral-400">— participant</span>
      </button>
    </div>
  </div>
</template>
