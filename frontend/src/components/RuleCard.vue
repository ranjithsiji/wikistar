<template>
  <div class="rule-card" :class="{ 'is-saved': !isDirty }">
    <div class="header">
      <div class="title-row">
        <span style="font-weight:700">{{ title }}</span>
        <div class="header-controls">
          <label class="checkbox-label"><input type="checkbox" v-model="rule.optional" /> optional</label>
          <label class="checkbox-label"><input type="checkbox" v-model="rule.showInJuryTool" /> show in jury tool</label>
          <button class="btn-remove" @click="$emit('remove')">✖</button>
        </div>
      </div>
    </div>
    
    <div v-if="!isDirty" class="saved-preview">
      <p>{{ getSavedPreview }}</p>
    </div>
    
    <div v-else class="body">
      <div v-if="rule.type === 'namespace'">
        <div class="form-row">
          <label>Article must belong to the</label>
          <select v-model="rule.config.namespace" class="input">
            <option value="Main">main namespace</option>
            <option value="Talk">Talk</option>
            <option value="User">User</option>
            <option value="Draft">Draft</option>
          </select>
        </div>
      </div>

      <div v-if="rule.type === 'size'">
        <div class="size-rule-group">
          <div class="form-row">
            <label>at least</label>
            <input v-model.number="rule.config.min" type="number" class="input input-number" />
            <select v-model="rule.config.metric" class="input">
              <option value="bytes">bytes</option>
              <option value="words">words</option>
              <option value="symbols">symbols</option>
            </select>
          </div>
        </div>

        <div v-if="rule.config.hasMax" class="size-rule-group">
          <div class="or-separator">- or -</div>
          <div class="form-row">
            <label>at most</label>
            <input v-model.number="rule.config.max" type="number" class="input input-number" />
            <select v-model="rule.config.maxMetric" class="input">
              <option value="bytes">bytes</option>
              <option value="words">words</option>
              <option value="symbols">symbols</option>
            </select>
            <button class="btn-remove-or" @click="toggleMaxSize">✖</button>
          </div>
        </div>

        <div v-if="!rule.config.hasMax" class="form-row">
          <label></label>
          <button class="btn-or" @click="toggleMaxSize">+ or...</button>
        </div>
      </div>

      <div v-if="rule.type === 'creation_date'">
        <div class="form-row">
          <label>not before</label>
          <input v-model="rule.config.notBefore" type="datetime-local" class="input" />
        </div>
        <div class="form-row">
          <label>not after</label>
          <input v-model="rule.config.notAfter" type="datetime-local" class="input" />
        </div>
      </div>

      <div v-if="rule.type === 'created_by_submitter'">
        <p class="rule-description">Only the creator can submit the article</p>
      </div>

      <div v-if="rule.type === 'submitter_registration'">
        <div class="form-row">
          <label>not before</label>
          <input v-model="rule.config.notBefore" type="date" class="input" />
        </div>
        <div class="form-row">
          <label>not after</label>
          <input v-model="rule.config.notAfter" type="date" class="input" />
        </div>
      </div>

      <div class="footer">
        <button class="btn btn-primary" @click="saveLocal">Save</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
const props = defineProps({ rule: Object })
const emit = defineEmits(['save','remove'])
const rule = props.rule
const titles = { 
  namespace:'Article namespace', 
  size:'Article size', 
  creation_date:'Article creation date', 
  created_by_submitter:'Created by submitter', 
  submitter_registration:'Submitter registration date' 
}
const title = titles[rule.type] || rule.type

function toggleMaxSize() {
  rule.config.hasMax = !rule.config.hasMax
}

const getSavedPreview = computed(() => {
  switch(rule.type) {
    case 'namespace':
      return `Article must belong to the ${rule.config.namespace} namespace`
    case 'size':
      let preview = `At least ${rule.config.min} ${rule.config.metric}`
      if(rule.config.hasMax) {
        preview += ` or at most ${rule.config.max} ${rule.config.maxMetric}`
      }
      return preview
    case 'creation_date':
      return `Created between ${rule.config.notBefore || 'any time'} and ${rule.config.notAfter || 'any time'}`
    case 'created_by_submitter':
      return 'Only the creator can submit the article'
    case 'submitter_registration':
      return `User registered between ${rule.config.notBefore || 'any time'} and ${rule.config.notAfter || 'any time'}`
    default:
      return 'Rule saved'
  }
})

function saveLocal(){
  rule._saved = true
  emit('save', rule)
}

// Status indicator: Saved vs Unsaved changes
const isDirty = computed(() => {
  return rule._saved !== true
})

// Flip to Unsaved when any field changes
watch(() => [rule.optional, rule.showInJuryTool, rule.config, rule.type], () => {
  rule._saved = false
}, { deep: true })

</script>

<style scoped>
.rule-card {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
  transition: all 0.3s ease;
}

.rule-card.is-saved {
  background: #f0f8ff;
  border: 2px solid #b0d4ff;
  padding: 8px 10px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  font-size: 0.9rem;
  font-weight: 600;
  color: #212529;
}

.header-controls {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.75rem;
  cursor: pointer;
  white-space: nowrap;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.saved-preview {
  padding: 6px 10px;
  background: #e7f5ff;
  border-left: 3px solid #0066cc;
  color: #0066cc;
  font-size: 0.8rem;
  border-radius: 4px;
  margin: 0;
}

.body {
  background: white;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.form-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-row label {
  min-width: 120px;
  font-size: 14px;
  color: #495057;
  font-weight: 500;
}

.input {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.input-number {
  width: 100px;
}

.btn-or {
  padding: 6px 12px;
  background: #e7f5ff;
  color: #0066cc;
  border: 1px solid #74c0fc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-or:hover {
  background: #d0ebff;
  border-color: #4da3ff;
}

.btn-remove-or {
  padding: 4px 8px;
  background: #ffe0e0;
  color: #d32f2f;
  border: 1px solid #ffb3b3;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-remove-or:hover {
  background: #ffb3b3;
  border-color: #ff8080;
}

.size-rule-group {
  background: #fafbfc;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e0e6ed;
  margin-bottom: 8px;
}

.or-separator {
  text-align: center;
  color: #6c757d;
  font-size: 13px;
  font-weight: 500;
  margin: 8px 0;
  letter-spacing: 2px;
}

.btn-remove {
  padding: 4px 8px;
  background: #ffe0e0;
  color: #d32f2f;
  border: 1px solid #ffb3b3;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-remove:hover {
  background: #ffb3b3;
  border-color: #ff8080;
}

.footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.btn-primary {
  background: #0066cc;
  color: white;
  border-color: #0052a3;
  font-weight: 500;
}

.btn-primary:hover {
  background: #0052a3;
  border-color: #003d7a;
}

.rule-description {
  margin: 8px 0;
  color: #495057;
  font-size: 14px;
}
</style>
