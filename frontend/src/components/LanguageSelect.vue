<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import LANGUAGES from '../languages'

// Searchable combobox over every language with a Wikipedia edition
// (from the Wikimedia sitematrix). v-model is the wiki code ("ml").
// Type to filter by code, autonym or English name; arrows + Enter to
// pick, Escape to close.
const model = defineModel({ type: String, default: '' })
const props = defineProps({
  placeholder: { type: String, default: 'Search language…' },
  // Wikipedia-project mode: options read "ml.wikipedia.org — മലയാളം".
  wiki: { type: Boolean, default: false }
})

const open = ref(false)
const query = ref('')
const active = ref(0)
const root = ref(null)
const listEl = ref(null)

function labelOf (l) {
  const name = l.name === l.en ? l.name : `${l.name} (${l.en})`
  return props.wiki ? `${l.code}.wikipedia.org — ${name}` : `${l.code} — ${name}`
}

const selectedLabel = computed(() => {
  const l = LANGUAGES.find(l => l.code === model.value)
  return l ? labelOf(l) : ''
})

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return LANGUAGES
  const starts = []
  const contains = []
  for (const l of LANGUAGES) {
    const hay = [l.code, l.name.toLowerCase(), l.en.toLowerCase()]
    if (hay.some(h => h.startsWith(q))) starts.push(l)
    else if (hay.some(h => h.includes(q))) contains.push(l)
  }
  return [...starts, ...contains]
})

watch(filtered, () => { active.value = 0 })

function openList () {
  open.value = true
  query.value = ''
}

function pick (l) {
  model.value = l.code
  open.value = false
}

function onKeydown (e) {
  if (!open.value && ['ArrowDown', 'Enter'].includes(e.key)) {
    e.preventDefault()
    openList()
    return
  }
  if (!open.value) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    active.value = Math.min(active.value + 1, filtered.value.length - 1)
    scrollActive()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    active.value = Math.max(active.value - 1, 0)
    scrollActive()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (filtered.value[active.value]) pick(filtered.value[active.value])
  } else if (e.key === 'Escape') {
    open.value = false
  }
}

function scrollActive () {
  requestAnimationFrame(() => {
    listEl.value?.querySelector('.active-option')
      ?.scrollIntoView({ block: 'nearest' })
  })
}

function onDocumentClick (e) {
  if (root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>

<template>
  <div ref="root" class="relative">
    <input class="input !pr-8" role="combobox" :aria-expanded="open"
           :value="open ? query : selectedLabel"
           :placeholder="open ? 'Type to search…' : (selectedLabel || placeholder)"
           @focus="openList" @click="openList"
           @input="query = $event.target.value"
           @keydown="onKeydown" />
    <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4
                text-neutral-500 dark:text-neutral-400 transition-transform"
         :class="open && 'rotate-180'" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="m6 9 6 6 6-6" />
    </svg>
    <div v-if="open" ref="listEl"
         class="absolute z-30 mt-1 w-full max-h-64 overflow-y-auto card shadow-lg py-1">
      <p v-if="!filtered.length" class="px-3 py-1.5 text-sm text-neutral-600 dark:text-neutral-300">
        No language matches "{{ query }}"
      </p>
      <button v-for="(l, i) in filtered" :key="l.code" type="button"
              class="block w-full text-left px-3 py-1.5 text-sm"
              :class="[i === active && 'active-option bg-neutral-100 dark:bg-neutral-800',
                       l.code === model && 'font-semibold text-blue-700 dark:text-blue-400']"
              @mouseenter="active = i" @click="pick(l)">
        {{ labelOf(l) }}
      </button>
    </div>
  </div>
</template>
