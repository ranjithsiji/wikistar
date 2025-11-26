<template>
  <div class="general-tab">
    <div class="form-section">
      <h3>Basic Information</h3>

      <div class="form-row">
        <label for="title">Title *</label>
        <input
          id="title"
          v-model="localData.title"
          type="text"
          class="form-input"
          placeholder="Enter editathon title"
          @input="updateParent"
        />
      </div>

      <div class="form-row">
        <label for="code">Code</label>
        <input
          id="code"
          v-model="localData.code"
          type="text"
          class="form-input"
          placeholder="Enter editathon code (optional)"
          @input="updateParent"
        />
      </div>

      <div class="form-row">
        <label for="project">Project</label>
        <select
          id="project"
          v-model="localData.project"
          class="form-select"
          @change="updateParent"
        >
          <option value="en.wikipedia.org">English Wikipedia</option>
          <option value="ml.wikipedia.org">Malayalam Wikipedia</option>
          <option value="es.wikipedia.org">Spanish Wikipedia</option>
          <option value="fr.wikipedia.org">French Wikipedia</option>
          <option value="de.wikipedia.org">German Wikipedia</option>
        </select>
      </div>

      <div class="form-row">
        <label for="description">Description</label>
        <textarea
          id="description"
          v-model="localData.description"
          class="form-textarea"
          placeholder="Enter editathon description"
          rows="4"
          @input="updateParent"
        ></textarea>
      </div>
    </div>

    <div class="form-section">
      <h3>Dates</h3>

      <div class="form-row">
        <label for="startDate">Start Date *</label>
        <input
          id="startDate"
          v-model="localData.startDate"
          type="date"
          class="form-input"
          @change="updateParent"
        />
      </div>

      <div class="form-row">
        <label for="endDate">End Date *</label>
        <input
          id="endDate"
          v-model="localData.endDate"
          type="date"
          class="form-input"
          @change="updateParent"
        />
      </div>
    </div>

    <div class="form-section">
      <h3>Settings</h3>

      <div class="form-row checkbox-row">
        <input
          id="consensualVote"
          v-model="localData.consensualVote"
          type="checkbox"
          class="form-checkbox"
          @change="updateParent"
        />
        <label for="consensualVote" class="checkbox-label">
          Consensual Vote
          <span class="help-text">Require consensus for article acceptance</span>
        </label>
      </div>

      <div class="form-row checkbox-row">
        <input
          id="hiddenMarks"
          v-model="localData.hiddenMarks"
          type="checkbox"
          class="form-checkbox"
          @change="updateParent"
        />
        <label for="hiddenMarks" class="checkbox-label">
          Hidden Marks
          <span class="help-text">Hide evaluation marks from participants</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const localData = reactive({
  title: '',
  code: '',
  project: 'en.wikipedia.org',
  description: '',
  startDate: '',
  endDate: '',
  consensualVote: false,
  hiddenMarks: false
})

// Watch for changes in props.editathon and update local data
watch(() => props.editathon, (newEditathon) => {
  if (newEditathon) {
    Object.assign(localData, {
      title: newEditathon.title || '',
      code: newEditathon.code || '',
      project: newEditathon.project || 'en.wikipedia.org',
      description: newEditathon.description || '',
      startDate: newEditathon.startDate || '',
      endDate: newEditathon.endDate || '',
      consensualVote: newEditathon.consensualVote || false,
      hiddenMarks: newEditathon.hiddenMarks || false
    })
  }
}, { immediate: true })

function updateParent() {
  emit('update', { ...localData })
}
</script>

<style scoped>
.general-tab {
  max-width: 600px;
}

.form-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.form-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 1.1em;
  font-weight: 600;
}

.form-row {
  margin-bottom: 15px;
}

.form-row label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s ease;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #1e88e5;
  box-shadow: 0 0 0 2px rgba(30, 136, 229, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.checkbox-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.form-checkbox {
  margin-top: 2px;
  width: 16px;
  height: 16px;
}

.checkbox-label {
  flex: 1;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.help-text {
  font-size: 12px;
  color: #666;
  font-weight: normal;
}
</style>
