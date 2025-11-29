# Create compact MarksTab with better UI
$marksTabContent = @'
<template>
  <div class="marks-content">
    <MarkSelector @add="addMark" />
    <h3>Please pick compulsory mark controls below to test the mark</h3>
    
    <!-- Added Controls Summary -->
    <div class="summary-section" v-if="hasSavedControls">
      <h4>Added Controls</h4>
      <div class="controls-list">
        <div v-if="toggleButton.saved" class="control-badge toggle-badge">
          <span>Toggle: {{ toggleButton.title || 'Untitled' }}</span>
          <button @click="removeToggleButton" class="badge-remove">×</button>
        </div>
        <div v-for="(radio, index) in savedRadioGroups" :key="index" class="control-badge radio-badge">
          <span>Radio: {{ radio.title || 'Untitled' }}</span>
          <button @click="removeRadioGroup(index)" class="badge-remove">×</button>
        </div>
        <div v-if="numericInput.saved" class="control-badge numeric-badge">
          <span>Numeric: {{ numericInput.title || 'Untitled' }}</span>
          <button @click="removeNumericInput" class="badge-remove">×</button>
        </div>
      </div>
    </div>

    <!-- Toggle Button Section -->
    <div v-if="toggleButton.visible" class="control-section compact" :class="{ saved: toggleButton.saved }">
      <div class="section-header">
        <h4>Toggle Button</h4>
        <button @click="removeToggleButton" class="btn-remove" v-if="toggleButton.saved">×</button>
        <div class="section-actions" v-else>
          <button @click="saveToggleButton" class="btn-save">Save</button>
          <button @click="cancelToggleButton" class="btn-cancel">Cancel</button>
        </div>
      </div>
      <div class="control-item" v-if="!toggleButton.saved">
        <div class="compact-controls">
          <input 
            type="text" 
            v-model="toggleButton.title" 
            placeholder="title" 
            class="compact-input"
          >
          <div class="value-control compact">
            <button @click="toggleButton.value--">-</button>
            <span class="value-display">{{ toggleButton.value }}</span>
            <button @click="toggleButton.value++">+</button>
          </div>
          <input 
            type="text" 
            v-model="toggleButton.description" 
            placeholder="description (optional)" 
            class="compact-input"
          >
        </div>
      </div>
      <div class="saved-indicator" v-else>
        ✓ Saved
      </div>
    </div>

    <!-- Radio Group Sections -->
    <div class="control-section compact" v-for="(radio, index) in radioGroups" :key="index" 
         :class="{ saved: radio.saved }">
      <div class="section-header">
        <h4>Radio Group {{ index + 1 }}</h4>
        <button @click="removeRadioGroup(index)" class="btn-remove" v-if="radio.saved">×</button>
        <div class="section-actions" v-else>
          <button @click="saveRadioGroup(index)" class="btn-save">Save</button>
          <button @click="cancelRadioGroup(index)" class="btn-cancel">Cancel</button>
        </div>
      </div>
      <div class="control-item" v-if="!radio.saved">
        <div class="compact-controls">
          <input 
            type="text" 
            v-model="radio.title" 
            placeholder="title" 
            class="compact-input"
          >
          <div class="value-control compact">
            <button @click="radio.value--">-</button>
            <span class="value-display">{{ radio.value }}</span>
            <button @click="radio.value++">+</button>
          </div>
          <input 
            type="text" 
            v-model="radio.description" 
            placeholder="description (optional)" 
            class="compact-input"
          >
        </div>
      </div>
      <div class="saved-indicator" v-else>
        ✓ Saved
      </div>
    </div>

    <!-- Numeric Input Section -->
    <div v-if="numericInput.visible" class="control-section compact" :class="{ saved: numericInput.saved }">
      <div class="section-header">
        <h4>Numeric Input</h4>
        <button @click="removeNumericInput" class="btn-remove" v-if="numericInput.saved">×</button>
        <div class="section-actions" v-else>
          <button @click="saveNumericInput" class="btn-save">Save</button>
          <button @click="cancelNumericInput" class="btn-cancel">Cancel</button>
        </div>
      </div>
      <div class="control-item" v-if="!numericInput.saved">
        <div class="compact-controls">
          <input 
            type="text" 
            v-model="numericInput.title" 
            placeholder="title" 
            class="compact-input"
          >
          <div class="numeric-controls compact">
            <div class="min-max">
              <label>min:</label>
              <div class="value-control compact">
                <button @click="numericInput.min--">-</button>
                <span class="value-display">{{ numericInput.min }}</span>
                <button @click="numericInput.min++">+</button>
              </div>
            </div>
            <div class="min-max">
              <label>max:</label>
              <div class="value-control compact">
                <button @click="numericInput.max--">-</button>
                <span class="value-display">{{ numericInput.max }}</span>
                <button @click="numericInput.max++">+</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="saved-indicator" v-else>
        ✓ Saved
      </div>
    </div>

    <!-- Preview Section -->
    <div class="preview-section compact">
      <div class="section-header">
        <h4>Preview</h4>
        <button @click="resetPreview" class="btn-cancel small">Reset</button>
      </div>
      <div class="preview-content">
        <p>Test your mark controls below:</p>
        
        <!-- Toggle Button Preview -->
        <div class="preview-control" v-if="toggleButton.saved">
          <label class="toggle-preview">
            <input type="checkbox" v-model="previewToggle">
            <span class="toggle-slider"></span>
            <span class="toggle-label">{{ toggleButton.title || 'Toggle' }}</span>
          </label>
          <span class="preview-value">{{ previewToggle ? toggleButton.value : 0 }}</span>
        </div>

        <!-- Radio Group Preview -->
        <div class="preview-control" v-for="(radio, index) in savedRadioGroups" :key="index">
          <label class="radio-preview">
            <input type="radio" :name="'radio-group'" v-model="previewRadio" :value="radio.value">
            <span class="radio-label">{{ radio.title || 'Radio ' + (index + 1) }}</span>
          </label>
          <span class="preview-value">{{ previewRadio === radio.value ? radio.value : '' }}</span>
        </div>

        <!-- Numeric Input Preview -->
        <div class="preview-control" v-if="numericInput.saved">
          <label class="numeric-preview">
            <span class="numeric-label">{{ numericInput.title || 'Number' }}:</span>
            <input 
              type="number" 
              v-model="previewNumeric" 
              :min="numericInput.min" 
              :max="numericInput.max"
              class="numeric-input"
            >
          </label>
          <span class="preview-value">{{ previewNumeric }}</span>
        </div>

        <div v-if="!hasSavedControls" class="no-controls">
          No controls added yet. Save some controls to see them here.
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue'
import MarkSelector from './MarkSelector.vue'

export default {
  name: 'MarksTab',
  components: { MarkSelector },
  props: {
    editathon: {
      type: Object,
      default: () => ({ id: 1, name: 'Editathon' })
    }
  },
  emits: ['update'],
  
  setup(props, { emit }) {
    // Mark controls data - start with null/empty to hide until selected
    const toggleButton = reactive({
      title: '',
      value: 0,
      description: '',
      saved: false,
      visible: false
    })

    const radioGroups = ref([])

    const numericInput = reactive({
      title: '',
      min: 1,
      max: 5,
      saved: false,
      visible: false
    })

    // Add via selector
    const addMark = (type) => {
      switch(type){
        case 'toggle':
          if (toggleButton.visible && !toggleButton.saved) {
            alert('Please save or cancel the current toggle button first')
            return
          }
          Object.assign(toggleButton, { title: '', value: 0, description: '', saved: false, visible: true })
          break
        case 'radio':
          radioGroups.value.push({ title: '', value: 0, description: '', saved: false })
          break
        case 'numeric':
          if (numericInput.visible && !numericInput.saved) {
            alert('Please save or cancel the current numeric input first')
            return
          }
          Object.assign(numericInput, { title: '', min: 1, max: 5, saved: false, visible: true })
          break
      }
      // Scroll to bottom where newly added control appears
      setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }), 50)
    }

    // Preview data
    const previewToggle = ref(false)
    const previewRadio = ref(0)
    const previewNumeric = ref(1)

    // Computed properties
    const hasSavedControls = computed(() => {
      return toggleButton.saved || numericInput.saved || radioGroups.value.some(r => r.saved)
    })

    const savedRadioGroups = computed(() => {
      return radioGroups.value.filter(r => r.saved)
    })

    const unsavedRadioGroups = computed(() => {
      return radioGroups.value.filter(r => !r.saved)
    })

    // Save functions
    const saveToggleButton = () => {
      if (!toggleButton.title.trim()) {
        alert('Please enter a title for the toggle button')
        return
      }
      toggleButton.saved = true
      emit('update', { type: 'toggleButton', data: { ...toggleButton } })
    }

    const removeToggleButton = () => {
      if (confirm('Remove this toggle button?')) {
        Object.assign(toggleButton, { title: '', value: 0, description: '', saved: false, visible: false })
        previewToggle.value = false
        emit('update', { type: 'toggleButton', data: null })
      }
    }

    const cancelToggleButton = () => {
      Object.assign(toggleButton, { title: '', value: 0, description: '', saved: false, visible: false })
    }

    const saveRadioGroup = (index) => {
      if (!radioGroups.value[index].title.trim()) {
        alert('Please enter a title for the radio group')
        return
      }
      radioGroups.value[index].saved = true
      emit('update', { type: 'radioGroup', index, data: { ...radioGroups.value[index] } })
    }

    const removeRadioGroup = (index) => {
      if (confirm('Remove this radio group?')) {
        radioGroups.value.splice(index, 1)
        if (previewRadio.value === radioGroups.value[index]?.value) {
          previewRadio.value = 0
        }
        emit('update', { type: 'radioGroup', index, data: null })
      }
    }

    const cancelRadioGroup = (index) => {
      Object.assign(radioGroups.value[index], { title: '', value: 0, description: '', saved: false })
    }

    const saveNumericInput = () => {
      if (!numericInput.title.trim()) {
        alert('Please enter a title for the numeric input')
        return
      }
      numericInput.saved = true
      emit('update', { type: 'numericInput', data: { ...numericInput } })
    }

    const removeNumericInput = () => {
      if (confirm('Remove this numeric input?')) {
        Object.assign(numericInput, { title: '', min: 1, max: 5, saved: false, visible: false })
        previewNumeric.value = 1
        emit('update', { type: 'numericInput', data: null })
      }
    }

    const cancelNumericInput = () => {
      Object.assign(numericInput, { title: '', min: 1, max: 5, saved: false, visible: false })
    }

    const addRadioGroup = () => {
      radioGroups.value.push({
        title: '',
        value: 0,
        description: '',
        saved: false
      })
    }

    const resetPreview = () => {
      previewToggle.value = false
      previewRadio.value = 0
      previewNumeric.value = 1
    }

    return {
      toggleButton,
      radioGroups,
      numericInput,
      addMark,
      previewToggle,
      previewRadio,
      previewNumeric,
      hasSavedControls,
      savedRadioGroups,
      unsavedRadioGroups,
      saveToggleButton,
      removeToggleButton,
      cancelToggleButton,
      saveRadioGroup,
      removeRadioGroup,
      cancelRadioGroup,
      saveNumericInput,
      removeNumericInput,
      cancelNumericInput,
      addRadioGroup,
      resetPreview
    }
  }
}
</script>

<style scoped>
.marks-content {
  padding: 1rem;
  max-width: 600px;
  margin: 0 auto;
}

h3 {
  color: #333;
  margin-bottom: 1.5rem;
  text-align: center;
  font-weight: normal;
  font-size: 1.1rem;
}

/* Summary Section */
.summary-section {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  border-left: 4px solid #2196F3;
}

.summary-section h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1rem;
}

.controls-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.control-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.toggle-badge {
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.radio-badge {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #bbdefb;
}

.numeric-badge {
  background: #fff3e0;
  color: #ef6c00;
  border: 1px solid #ffe0b2;
}

.badge-remove {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-remove:hover {
  opacity: 0.7;
}

/* Compact Control Sections */
.control-section.compact {
  margin-bottom: 1rem;
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  transition: all 0.3s ease;
}

.control-section.compact.saved {
  background: #f8f9fa;
  border-color: #4CAF50;
  border-left: 4px solid #4CAF50;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.section-header h4 {
  margin: 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.section-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-save {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
}

.btn-cancel {
  background: #757575;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-cancel.small {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.btn-remove {
  background: #f44336;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.compact-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.compact-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.value-control.compact {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-content: center;
}

.value-control.compact button {
  width: 28px;
  height: 28px;
  border: 1px solid #ccc;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.numeric-controls.compact {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}

.min-max {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.min-max label {
  font-size: 0.85rem;
  color: #666;
  min-width: auto;
}

.saved-indicator {
  color: #4CAF50;
  font-weight: 500;
  font-size: 0.9rem;
  text-align: center;
  padding: 0.5rem;
}

/* Add Section */
.add-section {
  text-align: center;
  margin: 1rem 0;
}

.add-btn {
  background: #2196F3;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

/* Preview Section */
.preview-section.compact {
  margin-top: 1.5rem;
  padding: 1rem;
  border: 2px dashed #ccc;
  border-radius: 8px;
  background: #f9f9f9;
}

.preview-content {
  margin-top: 0.5rem;
}

.preview-content p {
  margin: 0 0 0.75rem 0;
  color: #666;
  font-size: 0.9rem;
}

.preview-control {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  margin: 0.5rem 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.toggle-preview, .radio-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.toggle-slider {
  width: 36px;
  height: 18px;
  background: #ccc;
  border-radius: 18px;
  position: relative;
  transition: background 0.3s;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
}

input[type="checkbox"]:checked + .toggle-slider {
  background: #4CAF50;
}

input[type="checkbox"]:checked + .toggle-slider::after {
  transform: translateX(18px);
}

.radio-label, .toggle-label, .numeric-label {
  font-weight: 500;
  font-size: 0.9rem;
}

.numeric-input {
  width: 70px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
}

.preview-value {
  color: #2196F3;
  font-weight: 500;
  font-size: 0.9rem;
  min-width: 30px;
  text-align: right;
}

.no-controls {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px dashed #ddd;
}
</style>
'@

# Save the compact MarksTab
$marksTabContent | Set-Content -Path frontend\src\components\MarksTab.vue
Write-Host "✅ Created compact MarksTab with better visual feedback and X buttons"
