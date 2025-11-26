<template>
  <div class="rules-tab">
    <div class="rules-header">
      <h3>Rules</h3>
      <button class="btn btn-primary" @click="showRuleSelector = true">Add Rule</button>
    </div>

    <div v-if="localRules.length === 0" class="empty-state">
      <p>No rules added yet. Click "Add Rule" to create your first rule.</p>
    </div>

    <!-- Rules Accordion -->
    <div v-else class="rules-list">
      <div
        v-for="(rule, index) in localRules"
        :key="rule._uid || rule.id"
        class="rule-item"
      >
        <div class="rule-header" @click="toggleExpand(index)">
          <span class="rule-title">{{ getRuleTitle(rule.type) }}</span>
          <div class="rule-actions">
            <button class="btn-icon" @click.stop="removeRule(index)">✖</button>
          </div>
        </div>

        <transition name="expand">
          <div v-if="expandedRule === index" class="rule-body">
            <RuleCard
              :rule="rule"
              @update="updateRule(index, $event)"
            />
            <div class="rule-buttons">
              <button class="btn btn-outline" @click="saveSingleRule(index)">💾 Save</button>
            </div>
          </div>
        </transition>
      </div>
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
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { editathonsAPI } from '../wiki-forage-tool-/Frontend/src/api/editathons'
import RuleSelector from './RuleSelector.vue'
import RuleCard from './RuleCard.vue'

const props = defineProps({
  editathon: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['update'])

const localRules = ref([])
const showRuleSelector = ref(false)
const expandedRule = ref(null)

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

function getRuleTitle(type) {
  const titles = {
    namespace: 'Article Namespace',
    size: 'Article Size',
    creation_date: 'Article Creation Date',
    created_by_submitter: 'Created by Submitter',
    submitter_registration: 'Submitter Registration Date'
  }
  return titles[type] || 'Unknown Rule'
}

function toggleExpand(index) {
  expandedRule.value = expandedRule.value === index ? null : index
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

async function saveSingleRule(index) {
  const rule = localRules.value[index]
  try {
    await editathonsAPI.saveRule(props.editathon.id, rule)
    alert(`Rule "${getRuleTitle(rule.type)}" saved successfully!`)
  } catch (err) {
    console.error('Failed to save rule:', err)
    alert('Failed to save rule.')
  }
}

// Load existing rules
onMounted(async () => {
  if (props.editathon?.id) {
    try {
      const response = await editathonsAPI.getRules(props.editathon.id)
      localRules.value = (response.data || []).map(rule => ({
        ...rule,
        _uid: rule._uid || uid(),
        config: JSON.parse(rule.config || '{}')
      }))
    } catch (error) {
      console.error('Failed to load rules:', error)
    }
  }
})
</script>

<style scoped>
.rules-tab {
  max-width: 800px;
  margin: 0 auto;
}

.rules-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.rule-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
  background: white;
  transition: box-shadow 0.2s ease;
}

.rule-item:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.rule-header {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  background: #f7f9fc;
  border-bottom: 1px solid #eee;
}

.rule-title {
  font-weight: 600;
  color: #333;
}

.rule-actions .btn-icon {
  background: none;
  border: none;
  color: #777;
  font-size: 16px;
  cursor: pointer;
}

.rule-body {
  padding: 16px;
  background: #fff;
}

.rule-buttons {
  text-align: right;
  margin-top: 10px;
}

.btn {
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-primary {
  background: #3478f6;
  color: white;
  border: none;
}

.btn-outline {
  background: transparent;
  border: 1px solid #3478f6;
  color: #3478f6;
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex; align-items: center; justify-content: center;
}

.modal-content {
  background: #fff;
  border-radius: 10px;
  width: 400px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f3f3f3;
  border-bottom: 1px solid #ddd;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: scaleY(0);
  transform-origin: top;
}
</style>
