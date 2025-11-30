<template>
  <div class="marks-tab">
    <div class="marks-header">
      <h3>Mark Controls</h3>
      <MarkSelector @add="addMark" />
    </div>

    <div v-if="localMarks.length === 0" class="empty-state">
      <p>No marks added yet. Add a mark using the dropdown above.</p>
    </div>

    <div v-else class="marks-list">
      <MarkCard
        v-for="(mark, index) in localMarks"
        :key="mark.id"
        :mark="mark"
        :index="index"
        @save="(updated) => updateMark(index, updated)"
        @remove="() => removeMark(index)"
      />
    </div>

    <!-- Preview Section -->
    <div v-if="localMarks.length > 0" class="preview-section">
      <div class="preview-header">
        <h4>Preview</h4>
        <p>Please pick all compulsory mark controls below to test the mark</p>
      </div>
      
      <div class="preview-controls">
        <!-- Toggle Button Preview -->
        <div v-for="mark in localMarks.filter(m => m.type === 'toggle' && m._saved)" :key="'toggle-' + mark.id" class="preview-item">
          <label class="toggle-label">
            <input type="checkbox" v-model="previewValues[mark.id]" />
            <span class="toggle-slider"></span>
            <span>{{ mark.title }}</span>
          </label>
          <span class="preview-value">{{ previewValues[mark.id] ? mark.value : 0 }}</span>
        </div>

        <!-- Radio Group/Button Preview -->
        <div v-for="mark in localMarks.filter(m => (m.type === 'radio' || m.type === 'radio_button') && m._saved)" :key="'radio-' + mark.id" class="preview-item">
          <label class="radio-label">
            <input type="radio" name="mark-radio" :value="mark.id" v-model="selectedRadio" />
            <span>{{ mark.title }}</span>
          </label>
          <span class="preview-value">{{ selectedRadio === mark.id ? mark.value : 0 }}</span>
        </div>

        <!-- Numeric Input Preview -->
        <div v-for="mark in localMarks.filter(m => m.type === 'numeric' && m._saved)" :key="'numeric-' + mark.id" class="preview-item">
          <label class="numeric-label">
            <span>{{ mark.title }}:</span>
            <div class="numeric-input-wrapper">
              <button class="btn-spin" @click="previewValues[mark.id] = Math.max(mark.min || 0, previewValues[mark.id] - 1)">−</button>
              <input 
                type="number" 
                v-model.number="previewValues[mark.id]" 
                :min="mark.min" 
                :max="mark.max"
                class="preview-numeric-input"
              />
              <button class="btn-spin" @click="previewValues[mark.id] = Math.min(mark.max || 100, previewValues[mark.id] + 1)">+</button>
            </div>
          </label>
          <span class="preview-value">{{ previewValues[mark.id] }}</span>
        </div>
      </div>

      <!-- Accept/Reject Section -->
      <div class="preview-footer">
        <div class="preview-status">
          <span class="status-counter" v-if="articleAccepted === true">{{ acceptedCount }} (+1 accepted)</span>
          <span class="status-counter" v-else-if="articleAccepted === false">{{ rejectedCount }} (not accepted)</span>
          <span class="status-counter" v-else style="color: #999;">Select an option</span>
        </div>
        <div class="preview-question">Accept the article?:</div>
        <div class="preview-buttons">
          <button class="btn-yes" :class="{ active: articleAccepted === true }" @click="articleAccepted = true">Yes</button>
          <button class="btn-no" :class="{ active: articleAccepted === false && articleAccepted !== null }" @click="articleAccepted = false">No</button>
        </div>
        <button class="btn-reset" @click="resetPreview">Reset preview</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import MarkCard from './MarkCard.vue'
import MarkSelector from './MarkSelector.vue'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const localMarks = ref(
  Array.isArray(props.editathon?.marks) 
    ? props.editathon.marks.filter(m => m && m.type && ['toggle', 'radio', 'numeric'].includes(m.type))
    : []
)
const previewValues = ref({})
const selectedRadio = ref(null)
const articleAccepted = ref(null)
const acceptedCount = ref(1)
const rejectedCount = ref(0)

function resetPreview() {
  previewValues.value = {}
  selectedRadio.value = null
  articleAccepted.value = null
  acceptedCount.value = 1
  rejectedCount.value = 0
}

function addMark(type) {
  const validTypes = ['toggle', 'radio', 'numeric']
  const cleanType = String(type).trim()
  
  if (!cleanType || !validTypes.includes(cleanType)) {
    console.warn('Invalid mark type:', type)
    return
  }
  
  const newMark = {
    id: Date.now(),
    type: cleanType,
    title: '',
    value: 0,
    description: '',
    min: 1,
    max: 5,
    _saved: false
  }
  
  localMarks.value.push(newMark)
  emit('update', { marks: localMarks.value })
  
  // Scroll to newly added mark
  setTimeout(() => {
    const items = document.querySelectorAll('.mark-card')
    if (items && items.length) {
      items[items.length - 1].scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, 50)
}

function updateMark(index, updatedMark) {
  localMarks.value[index] = { ...updatedMark, _saved: true }
  emit('update', { marks: localMarks.value })
}

function removeMark(index) {
  localMarks.value.splice(index, 1)
  emit('update', { marks: localMarks.value })
}

watch(() => props.editathon?.marks, (newMarks) => {
  if (Array.isArray(newMarks)) {
    localMarks.value = newMarks.filter(m => m && m.type && ['toggle', 'radio', 'numeric'].includes(m.type))
  } else {
    localMarks.value = []
  }
})
</script>

<style scoped>
.marks-tab {
  max-width: 800px;
}

.marks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.marks-header h3 {
  margin: 0;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.marks-list {
  margin-bottom: 30px;
}

.preview-section {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-top: 30px;
}

.preview-header {
  margin-bottom: 20px;
}

.preview-header h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #212529;
}

.preview-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.preview-controls {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  gap: 12px;
}

.preview-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.toggle-label input[type="checkbox"] {
  display: none;
}

.toggle-slider {
  width: 40px;
  height: 20px;
  background: #ccc;
  border-radius: 20px;
  position: relative;
  display: inline-block;
  transition: background 0.3s;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
}

input[type="checkbox"]:checked + .toggle-slider {
  background: #0066cc;
}

input[type="checkbox"]:checked + .toggle-slider::after {
  transform: translateX(20px);
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.radio-label input[type="radio"] {
  cursor: pointer;
}

.numeric-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.numeric-input-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-spin {
  width: 28px;
  height: 28px;
  padding: 0;
  background: #f1f3f5;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-spin:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

.preview-numeric-input {
  width: 70px;
  padding: 6px 8px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}

.preview-value {
  color: #0066cc;
  font-weight: 600;
  font-size: 14px;
  min-width: 50px;
  text-align: right;
}

.preview-footer {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 16px;
  text-align: center;
}

.preview-status {
  font-size: 14px;
  color: #0066cc;
  font-weight: 600;
  margin-bottom: 12px;
}

.status-counter {
  display: inline-block;
}

.preview-question {
  font-size: 15px;
  font-weight: 500;
  color: #212529;
  margin-bottom: 12px;
}

.preview-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 12px;
}

.btn-yes {
  padding: 8px 24px;
  background: white;
  color: #495057;
  border: 2px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-yes:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.btn-yes.active {
  background: #0066cc;
  color: white;
  border-color: #0052a3;
}

.btn-yes.active:hover {
  background: #0052a3;
  border-color: #003d7a;
}

.btn-no {
  padding: 8px 24px;
  background: white;
  color: #495057;
  border: 2px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-no:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.btn-no.active {
  background: #f8f9fa;
  color: #212529;
  border-color: #adb5bd;
}

.btn-no.active:hover {
  background: #e9ecef;
  border-color: #868e96;
}

.btn-reset {
  display: block;
  margin: 0 auto;
  padding: 8px 16px;
  background: white;
  color: #495057;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-reset:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}
</style>
