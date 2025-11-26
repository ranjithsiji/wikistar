# Update the existing CreateEditathon component with Back/Next navigation
$createEditathonContent = @'
<template>
  <div class="container container-max py-4">
    <h2>Create New Editathon</h2>
    
    <!-- Progress Indicator -->
    <div class="progress-indicator mt-3">
      <div class="progress-steps d-flex justify-content-between">
        <div v-for="(tab, index) in tabs" :key="tab" 
             class="progress-step" :class="{ active: active === tab, completed: completedTabs.includes(tab) }">
          <div class="step-circle">{{ index + 1 }}</div>
          <div class="step-label">{{ tab }}</div>
        </div>
      </div>
    </div>

    <ul class="nav nav-tabs mt-3" role="tablist">
      <li class="nav-item" v-for="t in tabs" :key="t">
        <button type="button" class="nav-link" :class="{active: active===t}" @click="active=t">{{t}}</button>
      </li>
    </ul>

    <div class="card p-3 mt-2">
      <GeneralTab v-show="active === 'General'" :editathon="form" @update="updateForm" />
      <RulesTab v-show="active === 'Rules'" :editathon="form" @update="updateForm" />
      <MarksTab v-show="active === 'Marks'" :editathon="form" @update="updateForm" />
      <TemplateTab v-show="active === 'Template'" :editathon="form" @update="updateForm" />
      <JuryTab v-show="active === 'Jury'" :editathon="form" @update="updateForm" />
    </div>

    <div class="mt-3 d-flex justify-content-between align-items-center">
      <!-- Back Button -->
      <button type="button" class="btn btn-secondary" @click="goBack" :disabled="active === 'General'">
        ← Back
      </button>

      <!-- Progress Indicator -->
      <span class="text-muted">
        Step {{ currentStep }} of {{ tabs.length }}
      </span>

      <!-- Next/Save Button -->
      <button type="button" class="btn btn-primary" @click="goNext">
        {{ active === 'Jury' ? 'Create Editathon' : 'Next →' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { createEditathon } from '../services/api'
import GeneralTab from '../components/GeneralTab.vue'
import RulesTab from '../components/RulesTab.vue'
import MarksTab from '../components/MarksTab.vue'
import TemplateTab from '../components/TemplateTab.vue'
import JuryTab from '../components/JuryTab.vue'

const tabs = ['General','Rules','Marks','Template','Jury']
const active = ref('General')
const completedTabs = ref([])

const form = reactive({
  title: '',
  code: '',
  project: 'en.wikipedia.org',
  description: '',
  namespace: 'Main',
  minSize: 0,
  maxSize: 10000,
  startDate: '',
  endDate: '',
  createdBy: '',
  submissionDate: '',
  consensualVote: false,
  hiddenMarks: false,
  creatorSubmit: false,
  showInJury: false,
  rules: [],
  marks: [{ label: 'Accept', points: 1, hidden: false }],
  jury: [],
  template: {
    name: '',
    onThePage: 'no',
    created: false
  }
})

const currentStep = computed(() => tabs.indexOf(active.value) + 1)

function updateForm(updates) {
  Object.assign(form, updates)
}

function goBack() {
  const currentIndex = tabs.indexOf(active.value)
  if (currentIndex > 0) {
    active.value = tabs[currentIndex - 1]
  }
}

function goNext() {
  // Validate current tab before proceeding
  if (!validateCurrentTab()) {
    return
  }

  // Mark current tab as completed
  if (!completedTabs.value.includes(active.value)) {
    completedTabs.value.push(active.value)
  }

  const currentIndex = tabs.indexOf(active.value)
  if (currentIndex < tabs.length - 1) {
    // Go to next tab
    active.value = tabs[currentIndex + 1]
  } else {
    // Last tab - save everything
    saveAll()
  }
}

function validateCurrentTab() {
  switch (active.value) {
    case 'General':
      if (!form.title || !form.startDate || !form.endDate) {
        alert('Please fill in title, start date, and end date before proceeding.')
        return false
      }
      break
    case 'Jury':
      if (form.jury.length === 0) {
        alert('Please add at least one jury member before proceeding.')
        return false
      }
      break
  }
  return true
}

async function saveAll() {
  if (!form.title || !form.startDate || !form.endDate) {
    alert('Please fill general details first')
    active.value = 'General'
    return
  }
  
  const payload = {
    title: form.title,
    code: form.code,
    project: form.project,
    description: form.description,
    namespace: form.namespace,
    minSize: form.minSize,
    maxSize: form.maxSize,
    startDate: form.startDate,
    endDate: form.endDate,
    createdBy: form.createdBy,
    submissionDate: form.submissionDate,
    consensualVote: form.consensualVote,
    hiddenMarks: form.hiddenMarks,
    creatorSubmit: form.creatorSubmit,
    showInJury: form.showInJury,
    rules: form.rules.filter(r => r.text && r.text.trim()),
    marks: form.marks,
    jury: form.jury.filter(j => j.username && j.saved),
    template: form.template
  }
  
  try {
    const res = await createEditathon(payload)
    alert('Editathon created successfully!')
    const id = res.id || Math.floor(Math.random() * 1000) + 900
    window.location = `/editathon/${id}`
  } catch (error) {
    console.error('Failed to create editathon:', error)
    alert('Failed to create editathon. Please try again.')
  }
}
</script>

<style scoped>
.progress-indicator {
  margin-bottom: 1rem;
}

.progress-steps {
  position: relative;
}

.progress-steps::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #e9ecef;
  z-index: 1;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
}

.step-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 0.5rem;
  border: 3px solid white;
}

.progress-step.active .step-circle {
  background-color: #007bff;
  color: white;
}

.progress-step.completed .step-circle {
  background-color: #28a745;
  color: white;
}

.step-label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.progress-step.active .step-label {
  color: #007bff;
  font-weight: bold;
}

.progress-step.completed .step-label {
  color: #28a745;
}

/* Ensure the card has proper spacing */
.card {
  min-height: 400px;
}

/* Navigation buttons styling */
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  min-width: 120px;
}
</style>
'@

# Save the updated CreateEditathon component
$createEditathonContent | Set-Content -Path frontend\src\components\CreateEditathon.vue
Write-Host "✅ Updated CreateEditathon with Back/Next navigation and progress indicator"
