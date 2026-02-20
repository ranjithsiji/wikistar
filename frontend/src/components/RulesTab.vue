<template>
  <div class="rules-tab">
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
