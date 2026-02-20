<template>
  <div class="create-editathon-container">
    <div class="container">
      <div class="header-section">
        <h1 class="page-title">Edit Editathon</h1>
        <p class="page-subtitle">Update the details and resubmit for approval.</p>
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

      <div v-if="loadingData" class="loading-state">Loading editathon data...</div>

      <!-- Tab Content -->
      <div v-else class="tab-content-card">
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
          <button type="button" class="btn btn-secondary" @click="goBack" :disabled="active === 'General'">
            ← Back
          </button>

          <div class="footer-center">
            <div v-if="validationErrors.length > 0" class="validation-summary">
              <span class="error-icon">⚠️</span>
              <span>Please complete all required fields</span>
            </div>
          </div>

          <button type="button" class="btn btn-primary" @click="goNext" :disabled="isSubmitting">
            <span v-if="isSubmitting">
              <span class="spinner"></span> Saving...
            </span>
            <span v-else>
              {{ active === 'Jury' ? 'Save & Submit for Approval' : 'Next →' }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { updateEditathon } from '../services/api'
import GeneralTab from '../components/GeneralTab.vue'
import RulesTab from '../components/RulesTab.vue'
import MarksTab from '../components/MarksTab.vue'
import TemplateTab from '../components/TemplateTab.vue'
import JuryTab from '../components/JuryTab.vue'

import { store } from '../store'

const router = useRouter()
const route = useRoute()

const editathonId = computed(() => route.params.slug || route.params.id)

const tabs = ['General', 'Rules', 'Marks', 'Template', 'Jury']
const active = ref('General')
const completedTabs = ref([])
const validationErrors = ref([])
const isSubmitting = ref(false)
const loadingData = ref(true)

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
  rules: [],
  marks: [{ label: 'Accept', points: 1, hidden: false }],
  jury: [],
  template: { name: '', onThePage: 'no', created: false }
})

const currentStep = computed(() => tabs.indexOf(active.value) + 1)
const progressPercentage = computed(() => (currentStep.value / tabs.length) * 100)

onMounted(async () => {
  try {
    const res = await fetch(`/api/editathon/${editathonId.value}`)
    const data = await res.json()
    const e = data.editathon

    if (e) {
      form.title = e.name || ''
      form.code = e.code || ''
      form.wiki_language = e.wiki_language || e.language || ''
      form.project = e.wiki_domain || (form.wiki_language ? `${form.wiki_language}.wikipedia.org` : '')
      form.description = e.description || ''
      form.startDate = e.start_date ? e.start_date.split('T')[0] : ''
      form.endDate = e.end_date ? e.end_date.split('T')[0] : ''

      // Load marks config
      if (e.marks_config?.marks) {
        form.marks = e.marks_config.marks
        form.hiddenMarks = e.marks_config.hidden_marks || false
        form.consensualVote = e.marks_config.consensual_vote || false
      }

      // Load jury
      if (data.juries && data.juries.length > 0) {
        form.jury = data.juries.map(j => ({ username: j.username, saved: true }))
      }

      // Load rules
      if (e.rules && e.rules.length > 0) {
        form.rules = e.rules.map(r => ({
          type: r.type,
          config: r.config || {},
          description: r.description || ''
        }))
      }
    }

    completedTabs.value = [...tabs]
  } catch (err) {
    console.error('Failed to load editathon:', err)
    alert('Failed to load editathon data: ' + err.message)
  } finally {
    loadingData.value = false
  }
})

function updateForm(updates) {
  Object.assign(form, updates)
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
  return completedTabs.value.includes(tab) || Math.abs(targetIndex - currentIndex) <= 1
}

function navigateToTab(tab) {
  if (canNavigateToTab(tab)) {
    active.value = tab
  }
}

function validateCurrentTab() {
  const errors = []
  switch (active.value) {
    case 'General':
      if (!form.title?.trim()) errors.push('Title is required')
      if (!form.startDate) errors.push('Start date is required')
      if (!form.endDate) errors.push('End date is required')
      if (form.startDate && form.endDate && new Date(form.startDate) > new Date(form.endDate))
        errors.push('End date must be after start date')
      if (!form.description?.trim()) errors.push('Description is required')
      break
    case 'Rules':
      if (!form.rules.filter(r => r?.type).length) errors.push('Please add at least one rule')
      break
    case 'Marks':
      if (!form.marks?.length) errors.push('Please add at least one marking criteria')
      break
    case 'Jury':
      if (!form.jury.filter(j => j.username && j.saved).length)
        errors.push('Please add at least one jury member')
      break
  }
  return errors
}

function goNext() {
  const errors = validateCurrentTab()
  if (errors.length > 0) {
    validationErrors.value = errors
    alert(errors[0])
    return
  }
  validationErrors.value = []
  if (!completedTabs.value.includes(active.value)) completedTabs.value.push(active.value)

  const currentIndex = tabs.indexOf(active.value)
  if (currentIndex < tabs.length - 1) {
    active.value = tabs[currentIndex + 1]
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    saveAll()
  }
}

async function saveAll() {
  let allErrors = []
  for (const tab of tabs) {
    const backup = active.value
    active.value = tab
    allErrors = [...allErrors, ...validateCurrentTab()]
    active.value = backup
  }

  if (allErrors.length > 0) {
    alert('Please complete all required fields:\n\n' + allErrors.join('\n'))
    return
  }

  isSubmitting.value = true

  const payload = {
    title: form.title,
    code: form.code,
    project: form.project,
    wiki_language: form.wiki_language,
    description: form.description,
    namespace: form.namespace,
    minSize: form.minSize,
    maxSize: form.maxSize,
    startDate: form.startDate,
    endDate: form.endDate,
    createdBy: form.createdBy,
    consensualVote: form.consensualVote,
    hiddenMarks: form.hiddenMarks,
    rules: form.rules.filter(r => r?.type),
    marks: form.marks,
    jury: form.jury.filter(j => j.username && j.saved),
    template: form.template
  }

  try {
    await updateEditathon(editathonId.value, payload)
    alert('✅ Editathon updated and resubmitted for approval!')
    router.push('/personal-cabinet')
  } catch (error) {
    console.error('Failed to update editathon:', error)
    alert('❌ Failed to save changes:\n' + (error.message || 'Please try again.'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.create-editathon-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 2rem 0;
}
.container { max-width: 900px; margin: 0 auto; padding: 0 20px; }
.header-section { text-align: center; margin-bottom: 2rem; }
.page-title { font-size: 2.5rem; font-weight: 700; color: #2c3e50; margin-bottom: 0.5rem; }
.page-subtitle { color: #7f8c8d; font-size: 1.1rem; }
.loading-state { text-align: center; padding: 4rem; color: #6b7280; font-size: 1.1rem; }

.progress-indicator { margin-bottom: 2rem; }
.progress-bar-container { width: 100%; height: 8px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; margin-bottom: 2rem; }
.progress-bar { height: 100%; background: linear-gradient(90deg, #4CAF50, #45a049); transition: width 0.3s ease; border-radius: 10px; }
.progress-steps { display: flex; justify-content: space-between; }
.progress-step { display: flex; flex-direction: column; align-items: center; flex: 1; }
.progress-step.clickable { cursor: pointer; }
.step-circle { width: 50px; height: 50px; border-radius: 50%; background-color: #e9ecef; color: #6c757d; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-bottom: 0.5rem; border: 4px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: all 0.3s ease; font-size: 1.2rem; }
.progress-step.active .step-circle { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; transform: scale(1.15); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
.progress-step.completed .step-circle { background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; }
.step-label { font-size: 0.9rem; color: #6c757d; font-weight: 600; text-align: center; }
.progress-step.active .step-label { color: #667eea; font-weight: 700; }
.progress-step.completed .step-label { color: #4CAF50; }

.tab-content-card { background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }
.tab-header { padding: 1.5rem 2rem; border-bottom: 2px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.tab-header h2 { margin: 0; font-size: 1.8rem; font-weight: 600; }
.step-counter { background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600; }
.tab-body { padding: 2rem; min-height: 400px; }
.tab-footer { padding: 1.5rem 2rem; border-top: 2px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; background-color: #f8f9fa; }
.footer-center { flex: 1; display: flex; justify-content: center; }
.validation-summary { display: flex; align-items: center; gap: 0.5rem; color: #dc3545; font-size: 0.9rem; font-weight: 500; }

.btn { padding: 0.75rem 2rem; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; min-width: 130px; display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; }
.btn-secondary { background-color: #6c757d; color: white; }
.btn-secondary:hover:not(:disabled) { background-color: #5a6268; transform: translateY(-2px); }
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; box-shadow: 0 4px 12px rgba(102,126,234,0.3); }
.btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(102,126,234,0.4); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: white; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
