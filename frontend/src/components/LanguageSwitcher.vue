<template>
  <div class="language-selector me-3">
    <input
      type="text"
      class="form-control form-control-sm"
      placeholder="Language"
      v-model="searchQuery"
      @input="filterLanguages"
      @focus="showDropdown = true"
      @blur="hideDropdown"
    />
    <div v-if="showDropdown && filteredLanguages.length > 0" class="dropdown-menu show">
      <div
        v-for="language in displayedLanguages"
        :key="language.code"
        class="dropdown-item"
        :class="{ active: selectedLanguage?.code === language.code }"
        @mousedown="selectLanguage(language)"
      >
        <span v-if="language.code === 'all'">All Languages</span>
        <span v-else>{{ language.code }}: {{ language.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchWikimediaLanguages } from '../services/api'
import { store } from '../store'

const emit = defineEmits(['selected'])

const searchQuery = ref('')
const showDropdown = ref(false)
const selectedLanguage = ref(null)
const languages = ref([])

const filteredLanguages = computed(() => {
  // Always include "All" option at top if search matches "all" or is empty
  let list = [...languages.value]
  
  if (searchQuery.value) {
    list = list.filter(language =>
      language.code.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      language.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // Add "All" option at the beginning
  if (!searchQuery.value || 'all'.includes(searchQuery.value.toLowerCase())) {
     // Check if 'all' is already in the list to avoid duplicates if explicitly added to languages
     if (!list.some(l => l.code === 'all')) {
        list.unshift({ code: 'all', name: 'All' })
     }
  }
  
  return list
})

const displayedLanguages = computed(() => {
  return filteredLanguages.value // Show all matching languages to enable scrolling
})

function filterLanguages() {
  // Triggered on input
}

function selectLanguage(language) {
  if (language.code === 'all') {
    clearSelection()
    return
  }
  selectedLanguage.value = language
  searchQuery.value = `${language.code}: ${language.name}`
  showDropdown.value = false
  store.selectedLanguage = language.code
  try {
    localStorage.setItem('wikiLanguage', language.code)
  } catch (e) {
    console.warn('Failed to persist selected language:', e)
  }
  emit('selected', language.code)
}

function clearSelection() {
  selectedLanguage.value = null
  searchQuery.value = ''
  showDropdown.value = false
  store.selectedLanguage = null
  localStorage.removeItem('wikiLanguage')
  emit('selected', null)
}

function hideDropdown() {
  setTimeout(() => {
    showDropdown.value = false
  }, 200) // Delay to allow click on dropdown item
}

onMounted(async () => {
  // Use specific list from screenshot
  const specificLanguages = [
    { code: 'az', name: 'Azərbaycan' },
    { code: 'be', name: 'беларуская' },
    { code: 'bg', name: 'български' },
    { code: 'bn', name: 'বাংলা' },
    { code: 'cs', name: 'čeština' },
    { code: 'de', name: 'Deutsch' },
    { code: 'en', name: 'English' },
    { code: 'hu', name: 'magyar' },
    { code: 'id', name: 'Bahasa Indonesia' },
    { code: 'ja', name: '日本語' },
    { code: 'ka', name: 'ქართული' },
    { code: 'lo', name: 'ລາວ' },
    { code: 'ml', name: 'മലയാളം' },
    { code: 'ne', name: 'नेपाली भाषा' },
    { code: 'pt', name: 'português' },
    { code: 'ru', name: 'русский' },
    { code: 'sah', name: 'саха' },
    { code: 'sk', name: 'slovenčina' },
    { code: 'sq', name: 'Shqip' },
    { code: 'uk', name: 'українська' },
    { code: 'vi', name: 'Tiếng Việt' },
    { code: 'zh', name: '中文' }
  ]

  languages.value = specificLanguages
  
  // Pre-fill from stored selection if available
  try {
    const stored = localStorage.getItem('wikiLanguage')
    if (stored) {
      const match = languages.value.find(l => l.code === stored)
      if (match) {
        selectedLanguage.value = match
        searchQuery.value = `${match.code}: ${match.name}`
        store.selectedLanguage = match.code
      }
    }
  } catch (error) {
    console.error('Failed to load stored language:', error)
  }
})
</script>

<style scoped>
.language-selector {
  position: relative;
  display: inline-block;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
  display: block;
  min-width: 100%;
  padding: 0.5rem 0;
  margin: 0.125rem 0 0;
  font-size: 1rem;
  color: #212529;
  text-align: left;
  list-style: none;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 0.25rem;
  max-height: 300px; /* Enable scrolling */
  overflow-y: auto; /* Scrollbar */
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.175);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.25rem 1.5rem;
  clear: both;
  font-weight: 400;
  color: #212529;
  text-align: inherit;
  white-space: nowrap;
  background-color: transparent;
  border: 0;
  cursor: pointer;
}

.dropdown-item:hover, .dropdown-item:focus {
  color: #16181b;
  text-decoration: none;
  background-color: #f8f9fa;
}

.dropdown-item.active, .dropdown-item:active {
  color: #fff;
  text-decoration: none;
  background-color: #007bff; /* Blue background for active item */
}

.dropdown-menu.show {
  display: block;
}
</style>
