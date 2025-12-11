<template>
  <div class="jury-tab">
    <!-- Jury Members List -->
    <div class="jury-members-section">
      <transition-group name="jury-list" tag="div" class="jury-list">
        <div v-for="(jury, index) in localEditathon.jury" :key="index" class="jury-item" :class="{ 'saved': jury.saved }">
          <div class="jury-input-wrapper">
            <input 
              v-model="jury.username" 
              class="jury-input" 
              placeholder="Type Wikipedia username..."
              @input="onJuryInput(index, jury.username)"
              @focus="activeJuryIndex = index"
              @blur="hideJurySuggestions(index)"
              autocomplete="off"
            />
            <!-- Wikipedia Username Suggestions -->
            <div v-if="activeJuryIndex === index && jurySuggestions.length > 0" class="wiki-suggestions">
              <div 
                v-for="user in jurySuggestions" 
                :key="user.name"
                class="wiki-suggestion-item"
                @mousedown.prevent="selectJurySuggestion(index, user.name)"
              >
                <span class="suggestion-avatar">👤</span>
                <span class="suggestion-name">{{ user.name }}</span>
              </div>
            </div>
          </div>
          <button 
            class="btn-save-jury" 
            @click="saveJuryMember(index)"
            :disabled="!jury.username || jury.saved"
            :title="jury.saved ? 'Saved' : 'Save jury member'">
            ✓
          </button>
          <button 
            class="btn-remove-jury" 
            @click="removeJuryMember(index)"
            title="Remove jury member">
            ✕
          </button>
        </div>
      </transition-group>

      <button class="btn-add-jury" @click="addJuryMember">
        add
      </button>
    </div>

    <!-- Minimum Marks Per Article -->
    <div class="marks-setting">
      <label class="setting-label">
        Minimum number of marks per article:
      </label>
      <div class="number-control">
        <button 
          class="btn-decrement" 
          @click="decrementMarks"
          :disabled="localEditathon.minMarksPerArticle <= 1">
          −
        </button>
        <input 
          v-model.number="localEditathon.minMarksPerArticle" 
          class="marks-input" 
          type="number"
          min="1"
          max="20"
        />
        <button 
          class="btn-increment" 
          @click="incrementMarks"
          :disabled="localEditathon.minMarksPerArticle >= 20">
          +
        </button>
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

// Wikipedia username autocomplete
const jurySuggestions = ref([])
const activeJuryIndex = ref(-1)
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

// Fetch Wikipedia username suggestions
async function fetchWikiUserSuggestions(query) {
  if (!query || query.length < 2) {
    jurySuggestions.value = []
    return
  }

  try {
    // Use the wiki language from editathon settings, default to 'en'
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

function onJuryInput(index, username) {
  localEditathon.value.jury[index].saved = false
  activeJuryIndex.value = index
  
  // Debounce the API call
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchWikiUserSuggestions(username)
  }, 300)
}

function selectJurySuggestion(index, username) {
  localEditathon.value.jury[index].username = username
  localEditathon.value.jury[index].saved = false
  jurySuggestions.value = []
  activeJuryIndex.value = -1
}

function hideJurySuggestions(index) {
  // Delay hiding to allow click on suggestion
  setTimeout(() => {
    if (activeJuryIndex.value === index) {
      jurySuggestions.value = []
      activeJuryIndex.value = -1
    }
  }, 200)
}

function addJuryMember() {
  localEditathon.value.jury.push({ 
    username: '',
    saved: false
  })
}

function removeJuryMember(index) {
  localEditathon.value.jury.splice(index, 1)
}

function saveJuryMember(index) {
  const member = localEditathon.value.jury[index]
  if (member.username.trim()) {
    member.saved = true
  }
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
  padding: 0;
}

/* Jury Members Section */
.jury-members-section {
  margin-bottom: 2rem;
}

.jury-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.jury-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  padding: 0.5rem;
  transition: all 0.3s ease;
}

.jury-item:hover {
  border-color: #dee2e6;
  background: #f8f9fa;
}

.jury-item.saved {
  border-color: #28a745;
  background: #f8fff9;
}

.jury-input-wrapper {
  flex: 1;
  position: relative;
}

.jury-input {
  width: 100%;
  border: none;
  outline: none;
  padding: 0.5rem 0.75rem;
  font-size: 0.95rem;
  background: transparent;
}

.jury-input::placeholder {
  color: #adb5bd;
}

/* Wikipedia Username Suggestions Dropdown */
.wiki-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 2px solid #667eea;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.wiki-suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f0;
}

.wiki-suggestion-item:last-child {
  border-bottom: none;
}

.wiki-suggestion-item:hover {
  background: #f0f4ff;
}

.suggestion-avatar {
  font-size: 1rem;
  opacity: 0.7;
}

.suggestion-name {
  font-weight: 500;
  color: #333;
}

.btn-save-jury {
  width: 32px;
  height: 32px;
  border: 2px solid #28a745;
  background: white;
  color: #28a745;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.btn-save-jury:hover:not(:disabled) {
  background: #28a745;
  color: white;
}

.btn-save-jury:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-remove-jury {
  width: 32px;
  height: 32px;
  border: 2px solid #dc3545;
  background: white;
  color: #dc3545;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove-jury:hover {
  background: #dc3545;
  color: white;
}

.btn-add-jury {
  width: 100%;
  padding: 0.75rem;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-add-jury:hover {
  background: #667eea;
  color: white;
}

/* Marks Setting */
.marks-setting {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
}

.setting-label {
  font-weight: 600;
  color: #2c3e50;
  white-space: nowrap;
  font-size: 0.95rem;
}

.number-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.marks-input {
  width: 60px;
  padding: 0.5rem;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  text-align: center;
  font-size: 0.95rem;
  font-weight: 600;
}

.marks-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-decrement,
.btn-increment {
  width: 36px;
  height: 36px;
  border: 2px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.2rem;
  font-weight: 600;
  padding: 0;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-decrement:hover:not(:disabled),
.btn-increment:hover:not(:disabled) {
  background: #667eea;
  color: white;
  transform: scale(1.05);
}

.btn-decrement:disabled,
.btn-increment:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Animations */
.jury-list-enter-active,
.jury-list-leave-active {
  transition: all 0.3s ease;
}

.jury-list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.jury-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* Responsive */
@media (max-width: 768px) {
  .marks-setting {
    flex-direction: column;
    align-items: stretch;
  }

  .number-control {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }
}
</style>
