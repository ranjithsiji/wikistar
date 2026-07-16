<script setup>
// Editable scoring-rules table. v-model: array of rule objects (RuleIn shape).
// The label is a dropdown of the preset rule templates (single source of
// truth: the backend's default rule set) plus "Custom rule…"; picking a
// preset fills type/metric/points, custom rules stay fully editable.
const rules = defineModel({ type: Array, required: true })
const props = defineProps({ defaultRules: { type: Array, default: () => [] } })

const RULE_TYPES = ['per_unit', 'flat_bonus', 'suggested_list', 'threshold', 'eligibility']
const APPLIES = ['any', 'article', 'wikidata_item', 'commons_file']
const CUSTOM = '__custom__'

// Known claim/auto metrics. bytes_added is computed from the wiki
// automatically; the others are claimed by participants and verified.
const METRICS = [
  ['bytes_added', 'Bytes added (auto, from wiki history)'],
  ['substantial_improvement', 'Substantial improvement'],
  ['good_article', 'Good Article'],
  ['image_added', 'Image added'],
  ['reference_added', 'Reference added'],
  ['item_created', 'Wikidata item created'],
  ['statements', 'Wikidata statements added'],
  ['labels_descriptions_aliases', 'Labels / descriptions / aliases'],
  ['depicts_added', 'Depicts added (Commons)'],
]

const isPreset = (r) => props.defaultRules.some(t => t.label === r.label)

function onLabelPick (r, value) {
  if (value === CUSTOM) {
    r.label = ''
    return
  }
  const t = props.defaultRules.find(t => t.label === value)
  if (!t) return
  Object.assign(r, JSON.parse(JSON.stringify({
    unit_size: 1, points: 0, max_units: null, is_auto: false,
    params: null, metric: '', ...t
  })), { id: r.id, active: true })
}

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
    params: null, active: true, metric: '', ...JSON.parse(JSON.stringify(r))
  }))
}

const hasPoints = (r) => ['per_unit', 'flat_bonus', 'suggested_list'].includes(r.rule_type)

// ---- params helpers (no raw JSON in the UI) --------------------------------
function setParam (r, key, raw) {
  const v = parseInt(raw, 10)
  const params = { ...(r.params || {}) }
  if (v > 0) params[key] = v
  else delete params[key]
  r.params = Object.keys(params).length ? params : null
}

// eligibility: params.any_of = ["P17=Q668", ...] edited as P/Q pairs
const eligPairs = (r) => (r.params?.any_of || []).map(s => {
  const [p = '', q = ''] = String(s).split('=')
  return { p, q }
})
function writeElig (r, pairs) {
  r.params = { ...(r.params || {}), any_of: pairs.map(x => `${x.p}=${x.q}`) }
}
function setElig (r, i, key, value) {
  const pairs = eligPairs(r)
  pairs[i][key] = value.trim().toUpperCase()
  writeElig(r, pairs)
}
function addElig (r) { writeElig(r, [...eligPairs(r), { p: '', q: '' }]) }
function removeElig (r, i) {
  const pairs = eligPairs(r)
  pairs.splice(i, 1)
  writeElig(r, pairs)
}
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-3">
      <button type="button" class="btn" @click="addRule">+ Add rule</button>
      <button v-if="defaultRules.length" type="button" class="btn"
              @click="loadPreset(defaultRules)">Load self-assessment preset</button>
    </div>
    <p v-if="!rules.length" class="text-sm text-neutral-600 dark:text-neutral-300">
      No scoring rules yet. Jury-mode campaigns can work without rules; the
      self-assessment mode needs them.
    </p>
    <div v-for="(r, i) in rules" :key="i"
         class="card p-3 mb-2 grid gap-2 sm:grid-cols-12 items-end">
      <div class="sm:col-span-3">
        <label class="label">Rule</label>
        <select class="input" :value="isPreset(r) ? r.label : CUSTOM"
                @change="e => onLabelPick(r, e.target.value)">
          <option v-for="t in defaultRules" :key="t.label" :value="t.label">{{ t.label }}</option>
          <option :value="CUSTOM">Custom rule…</option>
        </select>
        <input v-if="!isPreset(r)" v-model="r.label" class="input mt-1"
               placeholder="Custom rule label" required />
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
        <select v-model="r.metric" class="input"
                @change="r.is_auto = r.metric === 'bytes_added'">
          <option value="">—</option>
          <option v-for="[value, label] in METRICS" :key="value" :value="value">
            {{ label }}
          </option>
        </select>
      </div>
      <div class="sm:col-span-1" v-if="r.rule_type === 'per_unit'">
        <label class="label">Per</label>
        <input v-model.number="r.unit_size" type="number" min="1" class="input" />
      </div>
      <div class="sm:col-span-1" v-if="hasPoints(r)">
        <label class="label">Points</label>
        <input v-model.number="r.points" type="number" step="0.5" class="input" />
      </div>
      <div class="sm:col-span-1" v-if="r.rule_type === 'flat_bonus'">
        <label class="label" title="Claim only counts when the submission added at least this many bytes">Min bytes</label>
        <input type="number" min="0" class="input" placeholder="—"
               :value="r.params?.min_bytes ?? ''"
               @input="e => setParam(r, 'min_bytes', e.target.value)" />
      </div>
      <div class="sm:col-span-2" v-if="r.rule_type === 'threshold'">
        <label class="label" title="New articles below this size earn no byte points">Min bytes</label>
        <input type="number" min="0" class="input" placeholder="e.g. 3500"
               :value="r.params?.min_new_article_bytes ?? ''"
               @input="e => setParam(r, 'min_new_article_bytes', e.target.value)" />
      </div>
      <div class="sm:col-span-1 flex justify-end">
        <button type="button" class="btn-danger" @click="rules.splice(i, 1)">✕</button>
      </div>

      <!-- eligibility: item must match any of these property=value pairs -->
      <div class="sm:col-span-12" v-if="r.rule_type === 'eligibility'">
        <label class="label">Item must match any of (Wikidata property = value)</label>
        <div v-for="(pair, pi) in eligPairs(r)" :key="pi" class="flex items-center gap-2 mb-1.5">
          <input class="input !w-32 font-mono" placeholder="P17" pattern="P[0-9]+"
                 title="A Wikidata property, e.g. P17"
                 :value="pair.p" @input="e => setElig(r, pi, 'p', e.target.value)" />
          <span class="text-neutral-500 dark:text-neutral-400">=</span>
          <input class="input !w-32 font-mono" placeholder="Q668" pattern="Q[0-9]+"
                 title="A Wikidata item, e.g. Q668"
                 :value="pair.q" @input="e => setElig(r, pi, 'q', e.target.value)" />
          <button type="button" class="btn !px-2 !py-0.5 text-xs" @click="removeElig(r, pi)">✕</button>
        </div>
        <button type="button" class="btn !py-1 text-xs" @click="addElig(r)">
          + add property = value
        </button>
      </div>
    </div>
  </div>
</template>
