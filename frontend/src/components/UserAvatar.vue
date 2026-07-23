<script setup>
import { computed } from 'vue'

// No photo data exists for any user (MediaWiki OAuth only gives us a
// username), so identity everywhere in the app is a colored initials
// circle instead — deterministic per username, not random per render.
const props = defineProps({
  username: { type: String, required: true },
  size: { type: String, default: 'md' }  // sm | md | lg
})

const COLORS = [
  'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300',
  'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300',
  'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
]
const SIZES = {
  sm: 'w-6 h-6 text-[10px]',
  md: 'w-8 h-8 text-xs',
  lg: 'w-16 h-16 text-xl'
}

const initials = computed(() => (props.username || '?').trim().slice(0, 2).toUpperCase())
const colorClass = computed(() => {
  let hash = 0
  for (const ch of props.username || '') hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return COLORS[hash % COLORS.length]
})
</script>

<template>
  <span class="inline-flex items-center justify-center rounded-full font-bold shrink-0"
        :class="[SIZES[size], colorClass]" :title="username">
    {{ initials }}
  </span>
</template>
