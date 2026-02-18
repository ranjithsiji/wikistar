<template>
  <div class="mark-card" :class="{ 'is-saved': !isDirty }">
    <div class="header">
      <div class="title-row">
        <span style="font-weight:700">{{ title }}</span>
        <button class="btn-remove" @click="$emit('remove')">✖</button>
      </div>
    </div>

    <div v-if="!isDirty" class="saved-preview">
      <p>✓ {{ getSavedPreview }}</p>
    </div>

    <div v-else class="body">
      <!-- Form content based on mark type -->
      <div v-if="['toggle', 'radio'].includes(mark.type)">
        <div class="form-row">
          <label>Title</label>
          <input v-model="mark.title" type="text" class="input" placeholder="Enter title" />
        </div>
        <div class="form-row">
          <label>Value</label>
          <div class="value-control">
            <button class="btn-spin" @click="mark.value--">−</button>
            <input v-model.number="mark.value" type="number" class="input input-value" />
            <button class="btn-spin" @click="mark.value++">+</button>
          </div>
        </div>
        <div class="form-row">
          <label>Description</label>
          <input v-model="mark.description" type="text" class="input" placeholder="optional" />
        </div>
      </div>

      <!-- Numeric Input -->
      <div v-else-if="mark.type === 'numeric'">
        <div class="form-row">
          <label>Title</label>
          <input v-model="mark.title" type="text" class="input" placeholder="Enter title" />
        </div>
        <div class="form-row">
          <label>Min</label>
          <div class="value-control">
            <button class="btn-spin" @click="mark.min--">−</button>
            <input v-model.number="mark.min" type="number" class="input input-value" />
            <button class="btn-spin" @click="mark.min++">+</button>
          </div>
          <label style="margin-left: 20px;">Max</label>
          <div class="value-control">
            <button class="btn-spin" @click="mark.max--">−</button>
            <input v-model.number="mark.max" type="number" class="input input-value" />
            <button class="btn-spin" @click="mark.max++">+</button>
          </div>
        </div>
      </div>

      <div v-else class="no-type-msg">
        Invalid mark type: {{ mark.type }}
      </div>

      <div class="footer">
        <button class="btn btn-primary" @click="saveLocal">Save</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'

const props = defineProps({ mark: Object })
const emit = defineEmits(['save', 'remove'])
const mark = props.mark

const titles = {
  'toggle': 'Toggle Button',
  'radio': 'Radio Group',
  'radio_button': 'Radio Button',
  'numeric': 'Numeric Input'
}
const title = computed(() => titles[mark.type] || mark.type || 'Mark Control')

const getSavedPreview = computed(() => {
  switch(mark.type) {
    case 'toggle':
      return `Toggle: "${mark.title}" = ${mark.value}${mark.description ? ' (' + mark.description + ')' : ''}`
    case 'radio':
      return `Radio: "${mark.title}" = ${mark.value}${mark.description ? ' (' + mark.description + ')' : ''}`
    case 'radio_button':
      return `Button: "${mark.title}" = ${mark.value}${mark.description ? ' (' + mark.description + ')' : ''}`
    case 'numeric':
      return `Numeric: "${mark.title}" (min: ${mark.min}, max: ${mark.max})`
    default:
      return 'Mark saved'
  }
})

function saveLocal(){
  mark._saved = true
  emit('save', mark)
}

const isDirty = computed(() => {
  return mark._saved !== true
})

watch(() => [mark.title, mark.value, mark.description, mark.min, mark.max], () => {
  mark._saved = false
}, { deep: true })
</script>

<style scoped>
.mark-card {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
  transition: all 0.3s ease;
}

.mark-card.is-saved {
  background: #f0f8ff;
  border: 2px solid #b0d4ff;
  padding: 8px 10px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #212529;
  flex: 1;
}

.btn-remove {
  padding: 3px 6px;
  background: #ffe0e0;
  color: #d32f2f;
  border: 1px solid #ffb3b3;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.btn-remove:hover {
  background: #ffb3b3;
  border-color: #ff8080;
}

.saved-preview {
  padding: 8px;
  background: #e7f5ff;
  border-left: 3px solid #0066cc;
  color: #0066cc;
  font-size: 0.8rem;
  border-radius: 4px;
  margin: 0;
  font-weight: 500;
}

.saved-preview p {
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
  min-width: 70px;
  font-size: 0.8rem;
  color: #495057;
  font-weight: 600;
}

.input {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
  flex: 1;
  min-width: 120px;
}

.input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.input-value {
  width: 70px;
  min-width: auto;
}

.value-control {
  display: flex;
  gap: 4px;
  align-items: center;
}

.btn-spin {
  padding: 6px 10px;
  background: #f1f3f5;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  transition: all 0.2s;
  min-width: 36px;
}

.btn-spin:hover {
  background: #e9ecef;
  border-color: #adb5bd;
  color: #212529;
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
  font-weight: 500;
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
  font-weight: 600;
}

.btn-primary:hover {
  background: #0052a3;
  border-color: #003d7a;
}

.no-type-msg {
  padding: 16px;
  text-align: center;
  color: #999;
  font-style: italic;
}
</style>
