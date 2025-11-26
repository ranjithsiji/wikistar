<template>
  <div class="rules-tab">
    <div class="rules-header">
      <h3>Rules</h3>
      <button class="btn btn-primary" @click="showRuleSelector = true">
        Add Rule
      </button>
    </div>

    <div v-if="localRules.length === 0" class="empty-state">
      <p>No rules added yet. Click "Add Rule" to create your first rule.</p>
    </div>

    <div v-else class="rules-list">
      <RuleCard
        v-for="(rule, index) in localRules"
        :key="rule._uid || rule.id"
        :rule="rule"
        @update="updateRule(index, $event)"
        @remove="removeRule(index)"
      />
    </div>

    <!-- Rule Selector Modal -->
    <div v-if="showRuleSelector" class="modal-overlay" @click="showRuleSelector = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>Add New Rule</h4>
          <button class="close-btn" @click="showRuleSelector = false">&times;</button>
        </div>
        <div class="modal-body">
          <RuleSelector @add="addRule" />
        </div>
      </div>
    </div>

    <!-- Preview Section -->
    <div class="preview-section">
      <h3>Rule Preview</h3>
      <div class="preview-form">
        <div class="form-row">
          <label for="previewUser">Test User</label>
          <input
            id="previewUser"
            v-model="previewUser"
            type="text"
            class="form-input"
            placeholder="Enter username"
          />
        </div>
        <div class="form-row">
          <label for="previewArticle">Test Article</label>
          <input
            id="previewArticle"
            v-model="previewArticle"
            type="text"
            class="form-input"
            placeholder="Enter article title"
          />
        </div>
        <div class="form-row">
          <button class="btn btn-outline" @click="showPreview">Test Rules</button>
        </div>
      </div>
      <div v-if="previewResult" class="preview-result">
        <h4>Preview Result:</h4>
        <pre>{{ previewResult }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { editathonsAPI } from '../api/editathons'
import RuleSelector from './RuleSelector.vue'
import RuleCard from './RuleCard.vue'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const localRules = ref([])
const showRuleSelector = ref(false)
const previewUser = ref('ExampleUser')
const previewArticle = ref('Example Article')
const previewResult = ref('')

function uid() {
  return '_' + Math.random().toString(36).slice(2, 9)
}

function addRule(type) {
  const newRule = {
    _uid: uid(),
    type,
    config: getDefaultConfig(type),
    optional: false,
    showInJuryTool: true
  }
  localRules.value.push(newRule)
  showRuleSelector.value = false
  updateParent()
}

function getDefaultConfig(type) {
  const configs = {
    namespace: { namespace: 0 },
    size: { minSize: 0, maxSize: 10000 },
    creation_date: { minDate: '', maxDate: '' },
    created_by_submitter: {},
    submitter_registration: { minDate: '', maxDate: '' }
  }
  return configs[type] || {}
}

function updateRule(index, updatedRule) {
  localRules.value[index] = { ...localRules.value[index], ...updatedRule }
  updateParent()
}

function removeRule(index) {
  localRules.value.splice(index, 1)
  updateParent()
}

function updateParent() {
  const rules = localRules.value.map(rule => ({
    ...rule,
    config: typeof rule.config === 'string' ? JSON.parse(rule.config) : rule.config
  }))
  emit('update', { rules })
}

function showPreview() {
  const results = []
  for (const rule of localRules.value) {
    const result = evaluateRule(rule, previewUser.value, previewArticle.value)
    results.push(`${rule.type}: ${result}`)
  }
  previewResult.value = results.join('\n')
}

function evaluateRule(rule, user, article) {
  // Simple mock evaluation - in real app this would call backend
  switch (rule.type) {
    case 'namespace':
      return `Article namespace check: ${rule.config.namespace}`
    case 'size':
      return `Size between ${rule.config.minSize} and ${rule.config.maxSize}`
    case 'creation_date':
      return `Created between ${rule.config.minDate || 'any'} and ${rule.config.maxDate || 'any'}`
    case 'created_by_submitter':
      return `Must be created by submitter`
    case 'submitter_registration':
      return `Submitter registered between ${rule.config.minDate || 'any'} and ${rule.config.maxDate || 'any'}`
    default:
      return 'Unknown rule type'
  }
}

// Watch for changes in props.editathon and update local rules
watch(() => props.editathon, (newEditathon) => {
  if (newEditathon && newEditathon.rules) {
    localRules.value = newEditathon.rules.map(rule => ({
      ...rule,
      _uid: rule._uid || uid(),
      config: typeof rule.config === 'string' ? JSON.parse(rule.config) : rule.config
    }))
  } else {
    localRules.value = []
  }
}, { immediate: true })

// Load rules from API if editathon has ID
onMounted(async () => {
  if (props.editathon && props.editathon.id && localRules.value.length === 0) {
    try {
      const response = await editathonsAPI.getRules(props.editathon.id)
      const rules = (response.data || []).map(rule => ({
        ...rule,
        _uid: `db_${rule.id}`,
        config: JSON.parse(rule.config || '{}')
      }))
      localRules.value = rules
    } catch (error) {
      console.error('Failed to load rules:', error)
    }
  }
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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.preview-section {
  margin-top: 30px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.preview-form {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 15px;
  align-items: end;
  margin-bottom: 20px;
}

.preview-result {
  background: white;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.preview-result pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
}
</style>
