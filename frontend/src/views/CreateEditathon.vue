<template>
  <div class="create-editathon-container">

    <div class="container">
      <div class="header-section">
        <h1 class="page-title">Create New Editathon</h1>
        <p class="page-subtitle">Fill in the details to create your editathon. All fields marked with * are required.</p>
      </div>
      
      <!-- Progress Indicator -->
      <div class="progress-indicator">
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <div class="progress-steps">
          <div v-for="(tab, index) in tabs" :key="tab" 
               class="progress-step" 
               :class="{ 
                 active: active === tab, 
                 completed: completedTabs.includes(tab),
                 clickable: canNavigateToTab(tab)
               }"
               @click="navigateToTab(tab)">
            <div class="step-circle">
              <span v-if="completedTabs.includes(tab)">✓</span>
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div class="step-label">{{ tab }}</div>
          </div>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="tab-content-card">
        <div class="tab-header">
          <h2>{{ active }}</h2>
          <span class="step-counter">Step {{ currentStep }} of {{ tabs.length }}</span>
        </div>

        <div class="tab-body">
          <GeneralTab v-show="active === 'General'" :editathon="form" @update="updateForm" />
          <RulesTab v-show="active === 'Rules'" :editathon="form" @update="updateForm" />
          <MarksTab v-show="active === 'Marks'" :editathon="form" @update="updateForm" />
          <TemplateTab v-show="active === 'Template'" :editathon="form" @update="updateForm" />
          <JuryTab v-show="active === 'Jury'" :editathon="form" @update="updateForm" />
        </div>

        <div class="tab-footer">
          <button 
            type="button" 
            class="btn btn-secondary" 
            @click="goBack" 
            :disabled="active === 'General'">
            ← Back
          </button>

          <div class="footer-center">
            <div v-if="validationErrors.length > 0" class="validation-summary">
              <span class="error-icon">⚠️</span>
              <span>Please complete all required fields</span>
            </div>
          </div>

          <button 
            type="button" 
            class="btn btn-primary" 
            @click="goNext"
            :disabled="isSubmitting">
            <span v-if="isSubmitting">
              <span class="spinner"></span> Creating...
            </span>
            <span v-else>
              {{ active === 'Jury' ? 'Submit for Approval' : 'Next →' }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createEditathon, fetchUserPendingEditathons } from '../services/api'
import { store } from '../store'
import GeneralTab from '../components/GeneralTab.vue'
import RulesTab from '../components/RulesTab.vue'
import MarksTab from '../components/MarksTab.vue'
import TemplateTab from '../components/TemplateTab.vue'
import JuryTab from '../components/JuryTab.vue'

const router = useRouter()
const tabs = ['General','Rules','Marks','Template','Jury']
const active = ref('General')
const completedTabs = ref([])
const validationErrors = ref([])
const isSubmitting = ref(false)
const currentUsername = computed(() => store.user?.username || 'Guest')


const form = reactive({
  title: '',
  code: '',
  project: '',
  wiki_language: '',
  description: '',
  namespace: 'Main',
  minSize: 0,
  maxSize: 10000,
  startDate: '',
  endDate: '',
  createdBy: store.user?.username || 'Guest',
  submissionDate: new Date().toISOString().split('T')[0],
  consensualVote: false,
  hiddenMarks: false,
  creatorSubmit: false,
  showInJury: false,
  status: 'pending', // New field for approval workflow
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
const progressPercentage = computed(() => (currentStep.value / tabs.length) * 100)

function updateForm(updates) {
  Object.assign(form, updates)
  // Auto-set wiki_language based on project
  if (updates.project) {
    form.wiki_language = updates.project.split('.')[0]
  }
  validationErrors.value = []
}

function goBack() {
  const currentIndex = tabs.indexOf(active.value)
  if (currentIndex > 0) {
    active.value = tabs[currentIndex - 1]
  }
}

function canNavigateToTab(tab) {
  const targetIndex = tabs.indexOf(tab)
  const currentIndex = tabs.indexOf(active.value)
  // Can navigate to completed tabs or adjacent tabs
  return completedTabs.value.includes(tab) || Math.abs(targetIndex - currentIndex) <= 1
}

function navigateToTab(tab) {
  if (canNavigateToTab(tab)) {
    active.value = tab
  }
}

function goNext() {
  // Validate current tab before proceeding
  const errors = validateCurrentTab()
  if (errors.length > 0) {
    validationErrors.value = errors
    // Show first error as alert
    alert(errors[0])
    return
  }

  validationErrors.value = []

  // Mark current tab as completed
  if (!completedTabs.value.includes(active.value)) {
    completedTabs.value.push(active.value)
  }

  const currentIndex = tabs.indexOf(active.value)
  if (currentIndex < tabs.length - 1) {
    // Go to next tab
    active.value = tabs[currentIndex + 1]
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    // Last tab - save everything
    saveAll()
  }
}

function validateCurrentTab() {
  const errors = []
  
  switch (active.value) {
    case 'General':
      if (!form.title || form.title.trim() === '') {
        errors.push('Title is required')
      }
      if (!form.startDate) {
        errors.push('Start date is required')
      }
      if (!form.endDate) {
        errors.push('End date is required')
      }
      if (form.startDate && form.endDate && new Date(form.startDate) > new Date(form.endDate)) {
        errors.push('End date must be after start date')
      }
      if (!form.description || form.description.trim() === '') {
        errors.push('Description is required')
      }
      break
      
    case 'Rules':
      const validRules = form.rules.filter(r => r && r.type)
      if (validRules.length === 0) {
        errors.push('Please add at least one rule')
      }
      break
      
    case 'Marks':
      if (!form.marks || form.marks.length === 0) {
        errors.push('Please add at least one marking criteria')
      }
      break
      
    case 'Jury':
      const savedJury = form.jury.filter(j => j.username && j.saved)
      if (savedJury.length === 0) {
        errors.push('Please add at least one jury member')
      }
      break
  }
  
  return errors
}

async function saveAll() {
  // Final validation
  let allErrors = []
  for (const tab of tabs) {
    const tabBackup = active.value
    active.value = tab
    const errors = validateCurrentTab()
    allErrors = [...allErrors, ...errors]
    active.value = tabBackup
  }
  
  if (allErrors.length > 0) {
    alert('Please complete all required fields:\n\n' + allErrors.join('\n'))
    return
  }
  
  isSubmitting.value = true
  
  const payload = {
    title: form.title,
    code: form.code || `editathon-${Date.now()}`,
    project: form.project,
    wiki_language: form.wiki_language,
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
    status: 'pending', // Set as pending for approval
    rules: form.rules.filter(r => r && r.type),
    marks: form.marks,
    jury: form.jury.filter(j => j.username && j.saved),
    template: form.template
  }
  
  try {
    const res = await createEditathon(payload)
    const slug = res.code || res.id
    
    // Show success message
    alert('✅ Editathon submitted successfully!\n\nYour editathon has been submitted for approval. You can track its status in your Personal Cabinet.\n\nOnce approved by a sysop on this project\'s wiki, it will appear in the ongoing editathons list.')
    
    // Redirect to the editathon page using slug
    router.push(`/editathon/${slug}`)
  } catch (error) {
    console.error('Failed to create editathon:', error)
    alert('❌ Failed to create editathon.\n\n' + (error.message || 'Please try again.'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.create-editathon-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 1rem 0;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 15px;
}

.header-section {
  text-align: center;
  margin-bottom: 1rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.page-subtitle {
  color: #7f8c8d;
  font-size: 0.85rem;
}

/* Progress Indicator */
.progress-indicator {
  margin-bottom: 1rem;
}

.progress-bar-container {
  width: 100%;
  height: 6px;
  background-color: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #45a049);
  transition: width 0.3s ease;
  border-radius: 10px;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  position: relative;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
  transition: all 0.3s ease;
}

.progress-step.clickable {
  cursor: pointer;
}

.progress-step.clickable:hover .step-circle {
  transform: scale(1.1);
}

.step-circle {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  background-color: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 0.3rem;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.progress-step.active .step-circle {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: scale(1.15);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.progress-step.completed .step-circle {
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
}

.step-label {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 600;
  text-align: center;
}

.progress-step.active .step-label {
  color: #667eea;
  font-weight: 700;
}

.progress-step.completed .step-label {
  color: #4CAF50;
}

/* Tab Content Card */
.tab-content-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.tab-header {
  padding: 0.75rem 1.25rem;
  border-bottom: 2px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.tab-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.step-counter {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.3rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.tab-body {
  padding: 1rem 1.25rem;
  min-height: 350px;
}

.tab-footer {
  padding: 0.75rem 1.25rem;
  border-top: 2px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
}

.footer-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.validation-summary {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #dc3545;
  font-size: 0.75rem;
  font-weight: 500;
}

.error-icon {
  font-size: 1.2rem;
}

/* Button Styling */
.btn {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 100px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #5a6268;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading Spinner */
.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive Design */
@media (max-width: 768px) {
  .create-editathon-container {
    padding: 1rem 0;
  }

  .page-title {
    font-size: 1.8rem;
  }

  .page-subtitle {
    font-size: 0.95rem;
  }

  .progress-steps {
    gap: 0.5rem;
  }

  .step-circle {
    width: 40px;
    height: 40px;
    font-size: 1rem;
  }

  .step-label {
    font-size: 0.75rem;
  }

  .tab-header {
    padding: 1rem;
    flex-direction: column;
    gap: 0.5rem;
  }

  .tab-header h2 {
    font-size: 1.4rem;
  }

  .tab-body {
    padding: 1.5rem;
  }

  .tab-footer {
    padding: 1rem;
    flex-direction: column;
    gap: 1rem;
  }

  .footer-center {
    order: -1;
  }

  .btn {
    width: 100%;
    min-width: unset;
  }
}

@media (max-width: 480px) {
  .step-label {
    display: none;
  }

  .container {
    padding: 0 10px;
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 450px;
  width: 90%;
}

.modal-body {
  padding: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-message {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #374151;
  line-height: 1.6;
}

.modal-question {
  margin: 0;
  font-size: 0.95rem;
  color: #6b7280;
  font-weight: 500;
}

.modal-footer {
  padding: 1.5rem 2rem;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn-modal {
  padding: 0.7rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-edit-draft {
  background: #667eea;
  color: white;
}

.btn-edit-draft:hover {
  background: #5568d3;
}

.btn-cancel {
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.btn-cancel:hover {
  background: #f9fafb;
}
</style>
'@

# Save the updated CreateEditathon component
$createEditathonContent | Set-Content -Path frontend\src\components\CreateEditathon.vue
Write-Host "✅ Updated CreateEditathon with Back/Next navigation and progress indicator"
