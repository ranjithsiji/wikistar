<template>
  <div class="template-tab">
    <!-- Automatically add template -->
    <div class="checkbox-section">
      <label class="checkbox-label">
        <input type="checkbox" v-model="localTemplate.autoAdd" @change="markUnsaved" />
        <span>Automatically add template</span>
      </label>
    </div>

    <!-- Template Configuration -->
    <div class="form-section">
      <div class="form-group">
        <label for="templateName">Template name</label>
        <input 
          id="templateName" 
          v-model="localTemplate.name" 
          @input="markUnsaved"
          class="input" 
          placeholder="Enter template name" 
        />
      </div>

      <div class="form-group">
        <label>Template placement</label>
        <div class="radio-group">
          <label class="radio-label">
            <input 
              type="radio" 
              v-model="localTemplate.placement" 
              @change="markUnsaved"
              value="article" 
            />
            <span>in the article</span>
          </label>
          <label class="radio-label">
            <input 
              type="radio" 
              v-model="localTemplate.placement" 
              @change="markUnsaved"
              value="talk" 
            />
            <span>on the talk page</span>
          </label>
        </div>
      </div>

      <div class="form-group">
        <label>Arguments</label>
        <div class="arguments-list">
          <div v-for="(arg, index) in localTemplate.arguments" :key="index" class="argument-row">
            <input 
              v-model="arg.key" 
              @input="markUnsaved"
              class="input arg-key" 
              placeholder="key" 
            />
            <span class="equals">=</span>
            <input 
              v-model="arg.value" 
              @input="markUnsaved"
              class="input arg-value" 
              placeholder="value" 
            />
            <button @click="removeArgument(index)" class="btn-remove">×</button>
          </div>
        </div>
        <button @click="addArgument" class="btn-add">add</button>
      </div>

      <!-- Preview Section -->
      <div class="preview-section">
        <label>Preview</label>
        <div class="preview-box">
          <code>{{ templatePreview }}</code>
        </div>
      </div>
    </div>

    <!-- Save Button with Status -->
    <div class="save-section">
      <span class="status-badge" :class="isSaved ? 'saved' : 'unsaved'">
        {{ isSaved ? 'Saved' : 'Unsaved' }}
      </span>
      <button v-if="!isSaved" @click="saveChanges" class="btn-save">
        Save
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const isSaved = ref(false)

const localTemplate = ref({
  autoAdd: props.editathon?.template?.autoAdd || false,
  name: props.editathon?.template?.name || '',
  placement: props.editathon?.template?.placement || 'talk',
  arguments: props.editathon?.template?.arguments || [{ key: '', value: '' }]
})

function addArgument() {
  localTemplate.value.arguments.push({ key: '', value: '' })
  markUnsaved()
}

function removeArgument(index) {
  localTemplate.value.arguments.splice(index, 1)
  if (localTemplate.value.arguments.length === 0) {
    localTemplate.value.arguments.push({ key: '', value: '' })
  }
  markUnsaved()
}

function markUnsaved() {
  isSaved.value = false
  updateParent()
}

function updateParent() {
  emit('update', { template: localTemplate.value, _templateSaved: isSaved.value })
}

function saveChanges() {
  isSaved.value = true
  updateParent()
}

const templatePreview = computed(() => {
  if (!localTemplate.value.name) return ''
  
  let preview = `{{${localTemplate.value.name}`
  
  // Add arguments with non-empty keys
  const validArgs = localTemplate.value.arguments.filter(arg => arg.key.trim())
  validArgs.forEach(arg => {
    preview += `|${arg.key}=${arg.value}`
  })
  
  preview += '}}'
  return preview
})

watch(() => props.editathon?.template, (newTemplate) => {
  if (newTemplate) {
    localTemplate.value = {
      autoAdd: newTemplate.autoAdd || false,
      name: newTemplate.name || '',
      placement: newTemplate.placement || 'talk',
      arguments: newTemplate.arguments?.length ? [...newTemplate.arguments] : [{ key: '', value: '' }]
    }
  }
}, { deep: true })

watch(() => props.editathon?._templateSaved, (newSaved) => {
  if (newSaved !== undefined) {
    isSaved.value = newSaved
  }
})
</script>

<style scoped>
.template-tab {
  max-width: 800px;
  padding: 0;
}

/* Checkbox Section */
.checkbox-section {
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  color: #2c3e50;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* Form Section */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.input {
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}

.input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Radio Group */
.radio-group {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.5rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  color: #495057;
}

.radio-label input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* Arguments */
.arguments-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.argument-row {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto;
  gap: 0.75rem;
  align-items: center;
}

.arg-key {
  max-width: 200px;
}

.arg-value {
  flex: 1;
}

.equals {
  font-weight: bold;
  color: #6c757d;
}

.btn-remove {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  transition: background 0.2s;
}

.btn-remove:hover {
  background: #c82333;
}

.btn-add {
  padding: 0.5rem 1rem;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  align-self: flex-start;
}

.btn-add:hover {
  background: #667eea;
  color: white;
}

/* Preview Section */
.preview-section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preview-section label {
  font-weight: 600;
  color: #2c3e50;
}

.preview-box {
  padding: 1rem;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  min-height: 60px;
}

.preview-box code {
  color: #495057;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  word-break: break-all;
}

/* Responsive */
@media (max-width: 768px) {
  .argument-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .equals {
    display: none;
  }
  
  .btn-remove {
    justify-self: end;
  }
  
  .arg-key {
    max-width: 100%;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 0.75rem;
  }
}

/* Save Section */
.save-section {
  margin-top: 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
}

.status-badge.saved {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-badge.unsaved {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.btn-save {
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-save:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
