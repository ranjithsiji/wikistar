<script setup>
// Editable scoring-rules table. v-model: array of rule objects (RuleIn shape).
const rules = defineModel({ type: Array, required: true })
defineProps({ defaultRules: { type: Array, default: () => [] } })

const RULE_TYPES = ['per_unit', 'flat_bonus', 'suggested_list', 'threshold', 'eligibility']
const APPLIES = ['any', 'article', 'wikidata_item']

function addRule () {
  rules.value.push({
    rule_type: 'flat_bonus', applies_to: 'any', label: '', metric: '',
    unit_size: 1, points: 1, max_units: null, is_auto: false,
    params: null, active: true
  })
}
function loadPreset (preset) {
  rules.value = preset.map(r => ({
    unit_size: 1, points: 0, max_units: null, is_auto: false,
    params: null, active: true, metric: '', ...r
  }))
}
const hasPoints = (r) => ['per_unit', 'flat_bonus', 'suggested_list'].includes(r.rule_type)
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-3">
      <button type="button" class="btn" @click="addRule">+ Add rule</button>
      <button v-if="defaultRules.length" type="button" class="btn"
              @click="loadPreset(defaultRules)">Load self-assessment preset</button>
    </div>
    <p v-if="!rules.length" class="text-sm text-neutral-500">
      No scoring rules yet. Jury-mode campaigns can work without rules; the
      self-assessment mode needs them.
    </p>
    <div v-for="(r, i) in rules" :key="i"
         class="card p-3 mb-2 grid gap-2 sm:grid-cols-12 items-end">
      <div class="sm:col-span-3">
        <label class="label">Label</label>
        <input v-model="r.label" class="input" placeholder="e.g. Content added" required />
      </div>
      <div class="sm:col-span-2">
        <label class="label">Type</label>
        <select v-model="r.rule_type" class="input">
          <option v-for="t in RULE_TYPES" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
      <div class="sm:col-span-2">
        <label class="label">Applies to</label>
        <select v-model="r.applies_to" class="input">
          <option v-for="a in APPLIES" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>
      <div class="sm:col-span-2" v-if="r.rule_type === 'per_unit' || r.rule_type === 'flat_bonus'">
        <label class="label">Metric</label>
        <input v-model="r.metric" class="input" placeholder="bytes_added" />
      </div>
      <div class="sm:col-span-1" v-if="r.rule_type === 'per_unit'">
        <label class="label">Per</label>
        <input v-model.number="r.unit_size" type="number" min="1" class="input" />
      </div>
      <div class="sm:col-span-1" v-if="hasPoints(r)">
        <label class="label">Points</label>
        <input v-model.number="r.points" type="number" step="0.5" class="input" />
      </div>
      <div class="sm:col-span-1 flex justify-end">
        <button type="button" class="btn-danger" @click="rules.splice(i, 1)">✕</button>
      </div>
      <div class="sm:col-span-12" v-if="r.rule_type === 'threshold' || r.rule_type === 'eligibility'">
        <label class="label">Parameters (JSON)</label>
        <input class="input font-mono text-xs"
               :value="JSON.stringify(r.params || {})"
               @change="e => { try { r.params = JSON.parse(e.target.value) } catch {} }" />
      </div>
    </div>
  </div>
</template>
