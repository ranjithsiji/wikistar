<script setup>
import { computed, reactive, ref } from 'vue'

// Jury review form rendered from the campaign's marks config
// (Fountain-style parts: radio / check / int). The server recomputes the
// total; the preview here is informational.
const props = defineProps({
  criteria: { type: Array, default: () => [] },
  existing: { type: Object, default: null }
})
const emit = defineEmits(['save'])

const scores = reactive({ ...(props.existing?.scores || {}) })
const total = ref(props.existing && !props.criteria.length ? props.existing.total : 0)
const decision = ref(props.existing?.decision || 'accept')
const comment = ref(props.existing?.comment || '')

const previewTotal = computed(() => {
  if (!props.criteria.length) return total.value
  let sum = 0
  for (const part of props.criteria) {
    const key = part.key || part.title
    const v = scores[key]
    if (v === undefined || v === null) continue
    if (part.type === 'radio' && part.values?.[v]) sum += Number(part.values[v].value || 0)
    else if (part.type === 'check' && v === true) sum += Number(part.value || 0)
    else if (part.type === 'int') sum += Number(v || 0)
  }
  return Math.round(sum * 100) / 100
})

function save () {
  emit('save', {
    scores: props.criteria.length ? { ...scores } : null,
    total: previewTotal.value,
    decision: decision.value,
    comment: comment.value || null
  })
}
</script>

<template>
  <form class="space-y-3" @submit.prevent="save">
    <div v-for="part in criteria" :key="part.key || part.title">
      <template v-if="part.type === 'radio'">
        <label class="label">{{ part.title }}</label>
        <select v-model.number="scores[part.key || part.title]" class="input">
          <option :value="undefined" disabled>—</option>
          <option v-for="(opt, i) in part.values" :key="i" :value="i">
            {{ opt.title }} ({{ opt.value }} pts)
          </option>
        </select>
      </template>
      <label v-else-if="part.type === 'check'" class="flex items-center gap-2 text-sm">
        <input type="checkbox" v-model="scores[part.key || part.title]" />
        {{ part.title }} (+{{ part.value }} pts)
      </label>
      <template v-else>
        <label class="label">{{ part.title }}</label>
        <input type="number" class="input" v-model.number="scores[part.key || part.title]" />
      </template>
    </div>

    <div v-if="!criteria.length">
      <label class="label">Points</label>
      <input type="number" step="0.5" class="input" v-model.number="total" />
    </div>

    <div class="flex gap-3 items-end">
      <div>
        <label class="label">Decision</label>
        <select v-model="decision" class="input">
          <option value="accept">Accept</option>
          <option value="reject">Reject</option>
          <option value="needs_work">Needs work</option>
        </select>
      </div>
      <div class="flex-1">
        <label class="label">Comment</label>
        <input class="input" v-model="comment" placeholder="Optional comment" />
      </div>
      <button type="submit" class="btn-primary">
        Save review ({{ previewTotal }} pts)
      </button>
    </div>
  </form>
</template>
