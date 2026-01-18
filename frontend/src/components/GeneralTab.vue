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
          @input="markUnsaved"
        />
      </div>

      <div class="form-row relative">
        <label for="project">Project</label>
        <input
          id="project"
          v-model="searchQuery"
          type="text"
          class="form-input"
          placeholder=""
          @input="onSearchInput"
          @blur="handleBlur"
          @focus="onSearchInput"
          autocomplete="off"
        />
        <div v-if="showDropdown && filteredSites.length > 0" class="dropdown-list">
          <div class="dropdown-header">
            <span class="col-code">Code</span>
            <span class="col-name">Name</span>
            <span class="col-lang">Language</span>
          </div>
          <div
            v-for="site in filteredSites"
            :key="site.domain"
            class="dropdown-item"
            @mousedown.prevent="selectProject(site)"
          >
            <span class="col-code">{{ site.languageCode }}</span>
            <span class="col-name">{{ site.projectName }}</span>
            <span class="col-lang">{{ site.languageName }}</span>
          </div>
        </div>
      </div>

      <div class="form-row">
        <label for="description">Description</label>
        <textarea
          id="description"
          v-model="localData.description"
          class="form-textarea"
          placeholder="Enter editathon description"
          rows="4"
          @input="markUnsaved"
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
          @change="markUnsaved"
        />
      </div>

      <div class="form-row">
        <label for="endDate">End Date *</label>
        <input
          id="endDate"
          v-model="localData.endDate"
          type="date"
          class="form-input"
          @change="markUnsaved"
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
          @change="markUnsaved"
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
          @change="markUnsaved"
        />
        <label for="hiddenMarks" class="checkbox-label">
          Hidden Marks
          <span class="help-text">Hide evaluation marks from participants</span>
        </label>
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
import { reactive, ref, watch, onMounted, computed } from 'vue'
import { fetchWikimediaLanguages, fetchWikimediaSites } from '../services/api'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const isSaved = ref(false)

const localData = reactive({
  title: '',
  code: '',
  project: '',
  description: '',
  startDate: '',
  endDate: '',
  consensualVote: false,
  hiddenMarks: false
})

const languages = ref([])
const sites = ref([])
const searchQuery = ref('')
const showDropdown = ref(false)

const filteredSites = computed(() => {
  if (!searchQuery.value) return []
  const query = searchQuery.value.toLowerCase()
  return sites.value.filter(site => 
    site.languageCode.toLowerCase().includes(query) ||
    site.projectName.toLowerCase().includes(query) ||
    site.languageName.toLowerCase().includes(query) ||
    site.domain.toLowerCase().includes(query)
  )
})

function onSearchInput() {
  showDropdown.value = true
  if (!searchQuery.value) {
    localData.project = ''
    markUnsaved()
  }
}

function selectProject(site) {
  localData.project = site.domain
  searchQuery.value = `${site.languageCode} - ${site.projectName} - ${site.languageName}`
  showDropdown.value = false
  markUnsaved()
}

function handleBlur() {
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

onMounted(async () => {
  try {
    // Load languages (may be used elsewhere) and sites for project select
    languages.value = await fetchWikimediaLanguages()
    sites.value = await fetchWikimediaSites()
  } catch (e) {
    console.error('Failed to load languages for project select:', e)
  }
})

// Watch for changes in props.editathon and update local data
watch(() => props.editathon, (newEditathon) => {
  if (newEditathon) {
    Object.assign(localData, {
      title: newEditathon.title || '',
      code: newEditathon.code || '',
      project: newEditathon.project || '',
      description: newEditathon.description || '',
      startDate: newEditathon.startDate || '',
      endDate: newEditathon.endDate || '',
      consensualVote: newEditathon.consensualVote || false,
      hiddenMarks: newEditathon.hiddenMarks || false
    })
    isSaved.value = newEditathon._generalSaved || false

    if (localData.project && sites.value.length > 0) {
       const site = sites.value.find(s => s.domain === localData.project)
       if (site) {
         searchQuery.value = `${site.languageCode} - ${site.projectName} - ${site.languageName}`
       } else {
         searchQuery.value = localData.project
       }
    } else if (!localData.project) {
        searchQuery.value = ''
    }
  }
}, { immediate: true })

watch(sites, () => {
  if (localData.project) {
     const site = sites.value.find(s => s.domain === localData.project)
     if (site) {
       searchQuery.value = `${site.languageCode} - ${site.projectName} - ${site.languageName}`
     }
  }
})

function markUnsaved() {
  isSaved.value = false
  updateParent()
}

function updateParent() {
  emit('update', { ...localData, _generalSaved: isSaved.value })
}

function saveChanges() {
  isSaved.value = true
  updateParent()
}

function onProjectChange() {
  markUnsaved()
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

.save-section {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
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
  padding: 10px 20px;
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

.relative {
  position: relative;
}

.dropdown-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.dropdown-header {
  display: flex;
  padding: 8px 12px;
  background: #f5f5f5;
  font-weight: bold;
  font-size: 12px;
  border-bottom: 1px solid #ddd;
  position: sticky;
  top: 0;
}

.dropdown-item {
  display: flex;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: #e3f2fd;
}

.col-code {
  flex: 0 0 60px;
  font-weight: 600;
}

.col-name {
  flex: 1;
}

.col-lang {
  flex: 1;
  text-align: right;
  color: #666;
}
</style>
