<template>
  <div class="rules-tab">
    <div class="rules-header">
      <h3>Eligibility Rules</h3>
      <RuleSelector @add="addRule" />
    </div>

    <div v-if="localRules.length === 0" class="empty-state">
      <p>No rules added yet. Add a rule using the dropdown above.</p>
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
      <div v-if="localRules.length > 0" class="preview">
        <h4>Preview</h4>
        <pre>{{ formattedPreview }}</pre>
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
  // Scroll to and visually focus newly added rule
  setTimeout(() => {
    const items = document.querySelectorAll('.rule-card')
    if (items && items.length) {
      items[items.length - 1].scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, 50)
}

function getDefaultConfig(type) {
  switch (type) {
    case 'namespace':
      return { namespace: 'Main' }
    case 'size':
      return { min: 1000, max: 10000 }
    case 'creation_date':
      return { notBefore: '', notAfter: '' }
    case 'created_by_submitter':
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
</script>

<style scoped>
.rules-tab {
  max-width: 800px;
}

.rules-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.rules-list {
  margin-bottom: 30px;
}
</style>
    optional: false,
