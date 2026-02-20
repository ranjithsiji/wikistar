<template>
  <div class="rules-tab">

    <!-- ── Jury Settings ── -->
    <div class="jury-settings-card mb-4">
      <h5 class="fw-bold mb-3">⚖️ Jury Settings</h5>
      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-label">Allow jury members to submit articles</div>
          <div class="setting-desc">When disabled, jury members who are part of this editathon cannot add articles — they can only review.</div>
        </div>
        <label class="toggle-switch" :class="{ active: juryCanSubmit }">
          <input type="checkbox" v-model="juryCanSubmit" @change="onJuryToggle" />
          <span class="toggle-knob"></span>
        </label>
      </div>
    </div>

    <div class="rules-header mb-3">
      <h5 class="fw-bold mb-0">Eligibility Rules</h5>
    </div>

    <RuleSelector @add="addRule" />

    <div v-if="localRules.length === 0" class="empty-state shadow-sm">
      <div class="display-6 opacity-25 mb-3">📋</div>
      <p class="mb-0">No rules added yet. Use the selector above to define what articles qualify for this editathon.</p>
    </div>

    <div v-else class="rules-list">
      <RuleCard
        v-for="(rule, index) in localRules"
        :key="rule.id"
        :rule="rule"
        :index="index"
        @save="(updated) => updateRule(index, updated)"
        @remove="() => removeRule(index)"
      />
    </div>

    <!-- Preview Section -->
    <div v-if="localRules.length > 0" class="mt-4 border-top pt-3">
      <button 
        class="btn btn-sm btn-link text-decoration-none p-0 text-muted" 
        @click="showPreview = !showPreview"
      >
        {{ showPreview ? 'Hide' : 'Show' }} JSON Preview Configuration
      </button>
      
      <div v-if="showPreview" class="preview mt-3">
        <div class="bg-dark rounded p-3">
          <pre class="text-info small mb-0 m-0 overflow-auto" style="max-height: 300px;">{{ formattedPreview }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import RuleCard from './RuleCard.vue'
import RuleSelector from './RuleSelector.vue'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const localRules = ref(Array.isArray(props.editathon?.rules) ? [...props.editathon.rules] : [])
const showPreview = ref(false)

// Jury submission toggle — derived from whether prevent_judge_submission rule is ABSENT
const juryCanSubmit = ref(
  !localRules.value.some(r => r.type === 'prevent_judge_submission')
)

function onJuryToggle() {
  // juryCanSubmit = true  → remove prevent_judge_submission rule if it exists
  // juryCanSubmit = false → add prevent_judge_submission rule if not already there
  if (juryCanSubmit.value) {
    const idx = localRules.value.findIndex(r => r.type === 'prevent_judge_submission')
    if (idx !== -1) localRules.value.splice(idx, 1)
  } else {
    const already = localRules.value.some(r => r.type === 'prevent_judge_submission')
    if (!already) {
      localRules.value.push({
        id: Date.now(),
        type: 'prevent_judge_submission',
        config: { required: true },
        optional: false,
        showInJuryTool: true
      })
    }
  }
  emit('update', { rules: localRules.value })
}

const formattedPreview = computed(() => {
  try {
    return JSON.stringify(localRules.value, null, 2)
  } catch (e) {
    return String(localRules.value)
  }
})

function addRule(type) {
  const newRule = {
    id: Date.now(),
    type,
    config: getDefaultConfig(type),
    optional: false,
    showInJuryTool: true
  }
  localRules.value.push(newRule)
  emit('update', { rules: localRules.value })
  
  setTimeout(() => {
    const items = document.querySelectorAll('.rule-card')
    if (items && items.length) {
      items[items.length - 1].scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, 50)
}

function toDatetimeLocal(dateStr) {
  if (!dateStr) return ''
  if (dateStr.includes('T')) return dateStr.slice(0, 16)
  return dateStr + 'T00:00'
}

function toDatetimeLocalEnd(dateStr) {
  if (!dateStr) return ''
  if (dateStr.includes('T')) return dateStr.slice(0, 16)
  return dateStr + 'T23:59'
}

function getDefaultConfig(type) {
  switch (type) {
    case 'namespace':
      return { namespace: 'Main' }
    case 'size':
      return { min: 1000, max: 10000, metric: 'bytes', maxMetric: 'bytes', hasMax: false }
    case 'creation_date':
      return {
        notBefore: toDatetimeLocal(props.editathon?.startDate),
        notAfter: toDatetimeLocalEnd(props.editathon?.endDate)
      }
    case 'created_by_submitter':
    case 'prevent_judge_submission':
      return { required: true }
    case 'submitter_registration':
      return { notBefore: '', notAfter: '' }
    default:
      return {}
  }
}

function updateRule(index, updatedRule) {
  localRules.value[index] = { ...updatedRule, _saved: true }
  emit('update', { rules: localRules.value })
}

function removeRule(index) {
  localRules.value.splice(index, 1)
  emit('update', { rules: localRules.value })
}

watch(() => props.editathon?.rules, (newRules) => {
  localRules.value = Array.isArray(newRules) ? [...newRules] : []
  juryCanSubmit.value = !localRules.value.some(r => r.type === 'prevent_judge_submission')
})

watch(
  () => [props.editathon?.startDate, props.editathon?.endDate],
  ([newStart, newEnd]) => {
    localRules.value.forEach(rule => {
      if (rule.type === 'creation_date') {
        rule.config.notBefore = toDatetimeLocal(newStart)
        rule.config.notAfter = toDatetimeLocalEnd(newEnd)
        rule._saved = false
      }
    })
    if (localRules.value.some(r => r.type === 'creation_date')) {
      emit('update', { rules: localRules.value })
    }
  }
)
</script>

<style scoped>
/* Jury Settings card */
.jury-settings-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 20px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.setting-info { flex: 1; }

.setting-label {
  font-weight: 600;
  font-size: 0.92rem;
  color: #111827;
  margin-bottom: 2px;
}

.setting-desc {
  font-size: 0.8rem;
  color: #6b7280;
  line-height: 1.4;
}

/* Toggle switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 46px;
  height: 26px;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-switch input { display: none; }

.toggle-knob {
  position: absolute;
  inset: 0;
  background: #d1d5db;
  border-radius: 26px;
  transition: background 0.2s;
}

.toggle-knob::after {
  content: '';
  position: absolute;
  top: 3px; left: 3px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,.25);
  transition: left 0.2s;
}

.toggle-switch.active .toggle-knob { background: #2563eb; }
.toggle-switch.active .toggle-knob::after { left: 23px; }

.rules-tab {
  max-width: 800px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #6c757d;
  background: white;
  border-radius: 12px;
  border: 1px dashed #dee2e6;
}

.rules-list {
  margin-bottom: 15px;
}

.preview pre {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  line-height: 1.5;
}
</style>
