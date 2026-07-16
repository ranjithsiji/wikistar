<script setup>
import { computed, reactive, ref } from 'vue'

// Jury review form rendered from the campaign's marks config
// (Fountain-style parts: radio / check / int), as inline button groups.
// When a marks config exists it carries the whole verdict — the review
// is always an accepting mark and the points say the rest (a "No" mark
// simply scores 0), exactly like Fountain. Only mark-less campaigns
// keep the explicit Accept / Reject decision next to the points box.
const props = defineProps({
  criteria: { type: Array, default: () => [] },
  existing: { type: Object, default: null }
})
const emit = defineEmits(['save'])

const scores = reactive({ ...(props.existing?.scores || {}) })
const total = ref(props.existing && !props.criteria.length ? props.existing.total : 0)
const decision = ref(props.existing?.decision || 'accept')
const comment = ref(props.existing?.comment || '')

const keyOf = (part) => part.key || part.title

const previewTotal = computed(() => {
  if (!props.criteria.length) return total.value
  let sum = 0
  for (const part of props.criteria) {
    const v = scores[keyOf(part)]
    if (v === undefined || v === null) continue
    if (part.type === 'radio' && part.values?.[v]) sum += Number(part.values[v].value || 0)
    else if (part.type === 'check' && v === true) sum += Number(part.value || 0)
    else if (part.type === 'int') sum += Number(v || 0)
  }
  return Math.round(sum * 100) / 100
})

function pickRadio (part, i) {
  const key = keyOf(part)
  scores[key] = scores[key] === i ? undefined : i
}

function save () {
  emit('save', {
    scores: props.criteria.length ? { ...scores } : null,
    total: previewTotal.value,
    // marks carry the verdict; the explicit decision exists only without them
    decision: props.criteria.length ? 'accept' : decision.value,
    comment: comment.value || null
  })
}
</script>

<template>
  <form class="flex flex-wrap items-end gap-x-5 gap-y-2" @submit.prevent="save">
    <div v-for="part in criteria" :key="keyOf(part)">
      <!-- radio group: one button per option -->
      <template v-if="part.type === 'radio'">
        <label class="label">{{ part.title }}</label>
        <div class="inline-flex rounded-lg border border-neutral-300 dark:border-neutral-700 overflow-hidden">
          <button v-for="(opt, i) in part.values" :key="i" type="button"
                  class="px-3 py-1.5 text-sm font-medium border-r last:border-r-0
                         border-neutral-300 dark:border-neutral-700 transition-colors"
                  :class="scores[keyOf(part)] === i
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-neutral-900 hover:bg-neutral-100 dark:hover:bg-neutral-800'"
                  :title="`${opt.value} pts`"
                  @click="pickRadio(part, i)">
            {{ opt.title }}
          </button>
        </div>
      </template>

      <!-- check: a single toggle button -->
      <button v-else-if="part.type === 'check'" type="button"
              class="rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors"
              :class="scores[keyOf(part)] === true
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'bg-white dark:bg-neutral-900 border-neutral-300 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800'"
              :title="`${part.value >= 0 ? '+' : ''}${part.value} pts`"
              @click="scores[keyOf(part)] = !scores[keyOf(part)]">
        {{ part.title }}
      </button>

      <!-- free number -->
      <template v-else>
        <label class="label">{{ part.title }}</label>
        <input type="number" class="input !w-24"
               v-model.number="scores[keyOf(part)]" />
      </template>
    </div>

    <template v-if="!criteria.length">
      <div>
        <label class="label">Points</label>
        <input type="number" step="0.5" class="input !w-24" v-model.number="total" />
      </div>
      <div>
        <label class="label">Decision</label>
        <select v-model="decision" class="input">
          <option value="accept">Accept</option>
          <option value="reject">Reject</option>
          <option value="needs_work">Needs work</option>
        </select>
      </div>
    </template>

    <div class="flex-1 min-w-44">
      <label class="label">Comment</label>
      <input class="input" v-model="comment" placeholder="Optional comment" />
    </div>
    <button type="submit" class="btn-primary whitespace-nowrap">
      Save review ({{ previewTotal }} pts)
    </button>
  </form>
</template>
