<template>
  <div class="jury-tab">
    <!-- Header Section -->
    <div class="jury-header mb-3">
      <h5 class="fw-bold mb-0">Jury Members</h5>
      <span class="badge bg-primary rounded-pill">{{ localEditathon.jury.length }} members</span>
    </div>

    <!-- Add Jury Member Input Area -->
    <div class="add-jury-container mb-4">
      <div class="input-group shadow-sm">
        <span class="input-group-text bg-white border-end-0">👤</span>
        <input 
          v-model="newJuryName" 
          class="form-control border-start-0 border-end-0" 
          placeholder="Enter Wikipedia username to add..."
          @input="onNewJuryInput"
          @keyup.enter="addNewJuryMember"
          autocomplete="off"
        />
        <button 
          class="btn btn-primary px-4 fw-bold" 
          @click="addNewJuryMember"
          :disabled="!newJuryName.trim()"
        >
          + Add
        </button>
      </div>

      <!-- Wikipedia Username Suggestions -->
      <div v-if="jurySuggestions.length > 0" class="wiki-suggestions shadow">
        <div 
          v-for="user in jurySuggestions" 
          :key="user.name"
          class="wiki-suggestion-item"
          @click="selectAndAddJury(user.name)"
        >
          <span class="suggestion-avatar">👤</span>
          <span class="suggestion-name">{{ user.name }}</span>
        </div>
      </div>
    </div>

    <!-- Jury Members List -->
    <div class="jury-members-list mb-5">
      <div v-if="localEditathon.jury.length === 0" class="empty-jury py-4 text-center border rounded-3 bg-light opacity-75">
        <p class="text-muted mb-0 small">No jury members added yet. Add users who will review articles.</p>
      </div>

      <transition-group name="jury-list" tag="div" class="d-flex flex-wrap gap-2">
        <div v-for="(jury, index) in localEditathon.jury" :key="jury.username" class="jury-badge shadow-sm">
          <span class="jury-avatar-mini me-2">👤</span>
          <span class="jury-name">{{ jury.username }}</span>
          <button 
            class="btn-remove-jury-mini ms-2" 
            @click="removeJuryMember(index)"
            title="Remove">
            ✕
          </button>
        </div>
      </transition-group>
    </div>

    <!-- Minimum Marks Per Article -->
    <div class="marks-setting p-4 border rounded-3 bg-white shadow-sm">
      <div class="row align-items-center">
        <div class="col-md-7">
          <h6 class="fw-bold mb-1">Review Quorum</h6>
          <p class="text-muted small mb-0">Minimum number of jury marks required to approve an article.</p>
        </div>
        <div class="col-md-5 d-flex justify-content-md-end mt-3 mt-md-0">
          <div class="input-group" style="width: 140px;">
            <button 
              class="btn btn-outline-primary" 
              type="button"
              @click="decrementMarks"
              :disabled="localEditathon.minMarksPerArticle <= 1">
              −
            </button>
            <input 
              v-model.number="localEditathon.minMarksPerArticle" 
              class="form-control text-center fw-bold" 
              type="text"
              readonly
            />
            <button 
              class="btn btn-outline-primary" 
              type="button"
              @click="incrementMarks"
              :disabled="localEditathon.minMarksPerArticle >= 20">
              +
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  editathon: Object
})

const emit = defineEmits(['update'])

const localEditathon = ref({ 
  ...props.editathon, 
  jury: props.editathon.jury || [],
  minMarksPerArticle: props.editathon.minMarksPerArticle || 1
})

const newJuryName = ref('')
const jurySuggestions = ref([])
let debounceTimer = null

watch(() => props.editathon, (newVal) => {
  localEditathon.value.jury = newVal.jury || []
  localEditathon.value.minMarksPerArticle = newVal.minMarksPerArticle || 1
}, { deep: true })

watch(() => localEditathon.value.jury, (newVal) => {
  emit('update', { jury: newVal })
}, { deep: true })

watch(() => localEditathon.value.minMarksPerArticle, (newVal) => {
  emit('update', { minMarksPerArticle: newVal })
})

async function fetchWikiUserSuggestions(query) {
  if (!query || query.length < 2) {
    jurySuggestions.value = []
    return
  }

  try {
    const lang = props.editathon?.wiki_language || props.editathon?.wikiLanguage || 'en'
    const url = `https://${lang}.wikipedia.org/w/api.php?action=query&list=allusers&auprefix=${encodeURIComponent(query)}&aulimit=6&format=json&origin=*`
    
    const response = await fetch(url)
    const data = await response.json()
    
    if (data.query && data.query.allusers) {
      jurySuggestions.value = data.query.allusers
    } else {
      jurySuggestions.value = []
    }
  } catch (error) {
    console.error('Error fetching Wikipedia users:', error)
    jurySuggestions.value = []
  }
}

function onNewJuryInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchWikiUserSuggestions(newJuryName.value)
  }, 300)
}

function selectAndAddJury(username) {
  newJuryName.value = username
  addNewJuryMember()
  jurySuggestions.value = []
}

function addNewJuryMember() {
  const name = newJuryName.value.trim()
  if (!name) return

  // Check if already exists
  if (localEditathon.value.jury.some(j => j.username.toLowerCase() === name.toLowerCase())) {
    newJuryName.value = ''
    jurySuggestions.value = []
    return
  }

  localEditathon.value.jury.push({ 
    username: name,
    saved: true
  })
  
  newJuryName.value = ''
  jurySuggestions.value = []
}

function removeJuryMember(index) {
  localEditathon.value.jury.splice(index, 1)
}

function incrementMarks() {
  if (localEditathon.value.minMarksPerArticle < 20) {
    localEditathon.value.minMarksPerArticle++
  }
}

function decrementMarks() {
  if (localEditathon.value.minMarksPerArticle > 1) {
    localEditathon.value.minMarksPerArticle--
  }
}
</script>

<style scoped>
.jury-tab {
  max-width: 800px;
}

.add-jury-container {
  position: relative;
}

.input-group-text, .form-control {
  border-color: #dee2e6;
}

.form-control:focus {
  box-shadow: none;
  border-color: #667eea;
}

/* Wikipedia Username Suggestions Dropdown */
.wiki-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 0 0 8px 8px;
  z-index: 1000;
  max-height: 250px;
  overflow-y: auto;
  margin-top: 2px;
}

.wiki-suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f8f9fa;
}

.wiki-suggestion-item:hover {
  background: #f0f4ff;
  color: #0645ad;
}

.suggestion-name {
  font-weight: 500;
}

/* Jury Badges */
.jury-badge {
  display: flex;
  align-items: center;
  background: #f8faff;
  border: 1px solid #d1d9e6;
  border-radius: 50px;
  padding: 0.4rem 1rem;
  transition: all 0.2s ease;
}

.jury-badge:hover {
  transform: translateY(-2px);
  border-color: #667eea;
}

.jury-name {
  font-weight: 600;
  color: #2d3748;
  font-size: 0.9rem;
}

.btn-remove-jury-mini {
  background: none;
  border: none;
  color: #a0aec0;
  font-size: 1rem;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  transition: all 0.2s;
}

.btn-remove-jury-mini:hover {
  background: #fed7d7;
  color: #e53e3e;
}

/* Animations */
.jury-list-enter-active,
.jury-list-leave-active {
  transition: all 0.3s ease;
}

.jury-list-enter-from {
  opacity: 0;
  transform: scale(0.9);
}

.jury-list-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

@media (max-width: 768px) {
  .marks-setting .row {
    text-align: center;
  }
}
</style>
