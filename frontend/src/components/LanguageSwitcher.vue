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
        @mousedown="selectLanguage(language)"
      >
        {{ language.code }}: {{ language.name }}
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
  if (searchQuery.value.length < 1) return []
  return languages.value.filter(language =>
    language.code.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    language.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const displayedLanguages = computed(() => {
  return filteredLanguages.value.slice(0, 6) // Show up to 6 suggestions
})

function filterLanguages() {
  // Triggered on input
}

function selectLanguage(language) {
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

function hideDropdown() {
  setTimeout(() => {
    showDropdown.value = false
  }, 150) // Delay to allow click on dropdown item
}

onMounted(async () => {
  try {
    const langs = await fetchWikimediaLanguages()
    languages.value = langs
    // Pre-fill from stored selection if available
    const stored = localStorage.getItem('wikiLanguage')
    if (stored) {
      const match = langs.find(l => l.code === stored)
      if (match) {
        selectedLanguage.value = match
        searchQuery.value = `${match.code}: ${match.name}`
        store.selectedLanguage = match.code
      }
    }
  } catch (error) {
    console.error('Failed to load languages:', error)
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
  display: none;
  min-width: 10rem;
  padding: 0.5rem 0;
  margin: 0;
  font-size: 1rem;
  color: #212529;
  text-align: left;
  list-style: none;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 0.25rem;
}

.dropdown-menu.show {
  display: block;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.25rem 1.5rem;
  clear: both;
  font-weight: 400;
  color: #212529;
  text-align: inherit;
  text-decoration: none;
  white-space: nowrap;
  background-color: transparent;
  border: 0;
  cursor: pointer;
}

.dropdown-item:hover {
  color: #16181b;
  text-decoration: none;
  background-color: #f8f9fa;
}
</style>
