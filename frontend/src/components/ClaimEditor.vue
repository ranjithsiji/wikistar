<script setup>
import { computed, reactive } from 'vue'

// Self-assessment claim editor: one row per claimable rule of the campaign.
// Auto rules (bytes added, suggested list) are computed by the server and
// shown read-only in the breakdown, not here.
const props = defineProps({
  rules: { type: Array, required: true },        // campaign rules
  submission: { type: Object, required: true }
})
const emit = defineEmits(['save'])

const AUTO_METRICS = ['bytes_added']
const claimable = computed(() =>
  props.rules.filter(r =>
    ['per_unit', 'flat_bonus'].includes(r.rule_type) &&
    !r.is_auto && !AUTO_METRICS.includes(r.metric) &&
    (r.applies_to === 'any' || r.applies_to === props.submission.kind)))

const state = reactive({})
for (const rule of claimable.value) {
  const existing = props.submission.claims.find(c => c.rule_id === rule.id)
  state[rule.id] = {
    checked: !!existing,
    quantity: existing?.quantity ?? (rule.rule_type === 'flat_bonus' ? 1 : 0),
    evidence_url: existing?.evidence_url || '',
    note: existing?.note || ''
  }
}

const preview = computed(() => {
  let sum = 0
  for (const rule of claimable.value) {
    const s = state[rule.id]
    if (!s.checked) continue
    if (rule.rule_type === 'flat_bonus') sum += Number(rule.points)
    else sum += Math.floor((s.quantity || 0) / rule.unit_size) * Number(rule.points)
  }
  return Math.round(sum * 100) / 100
})

function save () {
  const claims = claimable.value
    .filter(r => state[r.id].checked)
    .map(r => ({
      rule_id: r.id,
      quantity: r.rule_type === 'flat_bonus' ? 1 : (state[r.id].quantity || 0),
      evidence_url: state[r.id].evidence_url || null,
      note: state[r.id].note || null
    }))
  emit('save', claims)
}
</script>

<template>
  <form class="space-y-2" @submit.prevent="save">
    <p v-if="!claimable.length" class="text-sm text-neutral-500">
      This campaign has no claimable rules for this submission type.
    </p>
    <div v-for="rule in claimable" :key="rule.id"
         class="grid gap-2 sm:grid-cols-12 items-center text-sm">
      <label class="sm:col-span-4 flex items-center gap-2">
        <input type="checkbox" v-model="state[rule.id].checked" />
        {{ rule.label }}
        <span class="text-neutral-500 text-xs" v-if="rule.rule_type === 'per_unit'">
          ({{ rule.points }} pts / {{ rule.unit_size }})
        </span>
        <span class="text-neutral-500 text-xs" v-else>(+{{ rule.points }} pts)</span>
      </label>
      <div class="sm:col-span-2">
        <input v-if="rule.rule_type === 'per_unit'" type="number" min="0"
               class="input" v-model.number="state[rule.id].quantity"
               :disabled="!state[rule.id].checked" placeholder="quantity" />
      </div>
      <div class="sm:col-span-6">
        <input class="input" v-model="state[rule.id].evidence_url"
               :disabled="!state[rule.id].checked"
               placeholder="Evidence link (diff URL) — optional" />
      </div>
    </div>
    <div class="flex justify-end">
      <button type="submit" class="btn-primary">Save claims ({{ preview }} pts claimed)</button>
    </div>
  </form>
</template>
