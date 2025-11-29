<template>
  <div class="inspector-container">
    <div class="inspector-header">
      <h2>🔍 Wiki User Inspector</h2>
    </div>

    <div class="form-section">
      <div class="form-group">
        <label for="wikiSelect">
          <span class="step-number">1</span>
          Wikipedia Language
        </label>
        <div class="language-selector">
          <input
            type="text"
            id="wikiSelect"
            class="form-input"
            placeholder="Select language..."
            v-model="searchQuery"
            @input="filterLanguages"
            @focus="showDropdown = true"
            @blur="hideDropdown"
          />
          <div v-if="showDropdown && filteredWikis.length > 0" class="dropdown-menu show">
            <div
              v-for="wiki in displayedWikis"
              :key="wiki.value"
              class="dropdown-item"
              @mousedown="selectWiki(wiki)"
            >
              {{ wiki.name }}
            </div>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label for="usernameInput">
          <span class="step-number">2</span>
          Username
        </label>
        <input
          type="text"
          id="usernameInput"
          class="form-input"
          v-model="username"
          placeholder="Start typing to search..."
          autocomplete="off"
          @input="handleInput"
        >
        <div id="suggestions" class="suggestions-list" v-show="suggestions.length > 0">
          <div
            v-for="user in suggestions"
            :key="user.name"
            class="suggestion-item"
            @click="selectSuggestion(user.name)"
          >
            {{ user.name }}
          </div>
        </div>
      </div>

      <div class="button-group">
        <button class="validate-btn" @click="fetchStats" :disabled="loading">
          <span v-if="!loading">✓ Validate & Show Statistics</span>
          <span v-else>⏳ Connecting...</span>
        </button>
        <button class="reset-btn" @click="resetInspector" :disabled="loading" v-if="userData || error">
          ↺ Reset
        </button>
      </div>
    </div>

    <div class="loader-message" v-show="loading && !error">Connecting to Wikipedia...</div>
    <div class="error-message" v-show="error">{{ error }}</div>

    <div class="user-results" v-if="userData">
      <div class="user-header">
        <div class="user-avatar">{{ userData.name.charAt(0).toUpperCase() }}</div>
        <h3 class="user-name">{{ userData.name }}</h3>
      </div>

      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">User ID</span>
          <span class="stat-value">{{ userData.userid }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Edit Count</span>
          <span class="stat-value">{{ userData.editcount?.toLocaleString() }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Registered</span>
          <span class="stat-value">{{ formatRegistrationDate(userData.registration) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Status</span>
          <span class="stat-value" :class="userData.blockid ? 'status-blocked' : 'status-active'">
            {{ userData.blockid ? 'BLOCKED' : 'Active' }}
          </span>
        </div>
      </div>

      <div class="groups-section">
        <span class="groups-label">User Groups</span>
        <div class="groups-container">
          <span v-for="group in userData.groups" :key="group" class="group-badge">{{ group }}</span>
          <span v-if="!userData.groups || userData.groups.length === 0" class="no-groups">No groups</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const selectedWiki = ref('')
const username = ref('')
const suggestions = ref([])
const userData = ref(null)
const error = ref('')
const loading = ref(false)
const searchQuery = ref('')
const showDropdown = ref(false)

const filteredWikis = computed(() => {
  if (searchQuery.value.length < 1) return []
  return wikis.value.filter(wiki =>
    wiki.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    wiki.value.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const displayedWikis = computed(() => {
  return filteredWikis.value.slice(0, 4) // Limit to 4 suggestions
})

const wikis = ref([
  { name: 'English (English)', value: 'en' },
  { name: 'Spanish (español)', value: 'es' },
  { name: 'French (français)', value: 'fr' },
  { name: 'German (Deutsch)', value: 'de' },
  { name: 'Italian (italiano)', value: 'it' },
  { name: 'Portuguese (português)', value: 'pt' },
  { name: 'Russian (русский)', value: 'ru' },
  { name: 'Japanese (日本語)', value: 'ja' },
  { name: 'Chinese (中文)', value: 'zh' },
  { name: 'Arabic (العربية)', value: 'ar' },
  { name: 'Hindi (हिन्दी)', value: 'hi' },
  { name: 'Malayalam (മലയാളം)', value: 'ml' },
  { name: 'Tamil (தமிழ்)', value: 'ta' },
  { name: 'Telugu (తెలుగు)', value: 'te' },
  { name: 'Kannada (ಕನ್ನಡ)', value: 'kn' },
  { name: 'Bengali (বাংলা)', value: 'bn' },
  { name: 'Punjabi (ਪੰਜਾਬੀ)', value: 'pa' },
  { name: 'Marathi (मराठी)', value: 'mr' },
  { name: 'Gujarati (ગુજરાતી)', value: 'gu' },
  { name: 'Oriya (ଓଡ଼ିଆ)', value: 'or' },
  { name: 'Assamese (অসমীয়া)', value: 'as' },
  { name: 'Maithili (मैथिली)', value: 'mai' },
  { name: 'Santali (ᱥᱟᱱᱛᱟᱲᱤ)', value: 'sat' },
  { name: 'Kashmiri (कॉशुर / کٲشُر)', value: 'ks' },
  { name: 'Nepali (नेपाली)', value: 'ne' },
  { name: 'Sindhi (سنڌي، سندھی)', value: 'sd' },
  { name: 'Konkani (कोंकणी)', value: 'kok' },
  { name: 'Dogri (डोगरी)', value: 'doi' },
  { name: 'Manipuri (মৈতৈলোন্)', value: 'mni' },
  { name: 'Bodo (बड़ो)', value: 'brx' },
  { name: 'Sanskrit (संस्कृतम्)', value: 'sa' },
  { name: 'Urdu (اردو)', value: 'ur' },
  { name: 'Persian (فارسی)', value: 'fa' },
  { name: 'Turkish (Türkçe)', value: 'tr' },
  { name: 'Dutch (Nederlands)', value: 'nl' },
  { name: 'Polish (polski)', value: 'pl' },
  { name: 'Ukrainian (українська)', value: 'uk' },
  { name: 'Czech (čeština)', value: 'cs' },
  { name: 'Swedish (svenska)', value: 'sv' },
  { name: 'Danish (dansk)', value: 'da' },
  { name: 'Norwegian (norsk)', value: 'no' },
  { name: 'Finnish (suomi)', value: 'fi' },
  { name: 'Hungarian (magyar)', value: 'hu' },
  { name: 'Romanian (română)', value: 'ro' },
  { name: 'Bulgarian (български)', value: 'bg' },
  { name: 'Greek (Ελληνικά)', value: 'el' },
  { name: 'Hebrew (עברית)', value: 'he' },
  { name: 'Thai (ไทย)', value: 'th' },
  { name: 'Vietnamese (Tiếng Việt)', value: 'vi' },
  { name: 'Korean (한국어)', value: 'ko' },
  { name: 'Indonesian (Bahasa Indonesia)', value: 'id' },
  { name: 'Malay (Bahasa Melayu)', value: 'ms' },
  { name: 'Filipino (Filipino)', value: 'tl' },
  { name: 'Swahili (Kiswahili)', value: 'sw' },
  { name: 'Amharic (አማርኛ)', value: 'am' },
  { name: 'Hausa (Hausa)', value: 'ha' },
  { name: 'Yoruba (Yorùbá)', value: 'yo' },
  { name: 'Igbo (Igbo)', value: 'ig' },
  { name: 'Zulu (isiZulu)', value: 'zu' },
  { name: 'Xhosa (isiXhosa)', value: 'xh' },
  { name: 'Afrikaans (Afrikaans)', value: 'af' },
  { name: 'Catalan (català)', value: 'ca' },
  { name: 'Basque (euskara)', value: 'eu' },
  { name: 'Galician (galego)', value: 'gl' },
  { name: 'Welsh (Cymraeg)', value: 'cy' },
  { name: 'Irish (Gaeilge)', value: 'ga' },
  { name: 'Scottish Gaelic (Gàidhlig)', value: 'gd' },
  { name: 'Breton (brezhoneg)', value: 'br' },
  { name: 'Corsican (corsu)', value: 'co' },
  { name: 'Frisian (Frysk)', value: 'fy' },
  { name: 'Luxembourgish (Lëtzebuergesch)', value: 'lb' },
  { name: 'Occitan (occitan)', value: 'oc' },
  { name: 'Sardinian (sardu)', value: 'sc' },
  { name: 'Sicilian (sicilianu)', value: 'scn' },
  { name: 'Serbian (српски / srpski)', value: 'sr' },
  { name: 'Croatian (hrvatski)', value: 'hr' },
  { name: 'Bosnian (bosanski)', value: 'bs' },
  { name: 'Slovenian (slovenščina)', value: 'sl' },
  { name: 'Slovak (slovenčina)', value: 'sk' },
  { name: 'Lithuanian (lietuvių)', value: 'lt' },
  { name: 'Latvian (latviešu)', value: 'lv' },
  { name: 'Estonian (eesti)', value: 'et' },
  { name: 'Belarusian (беларуская)', value: 'be' },
  { name: 'Macedonian (македонски)', value: 'mk' },
  { name: 'Albanian (shqip)', value: 'sq' },
  { name: 'Armenian (Հայերեն)', value: 'hy' },
  { name: 'Georgian (ქართული)', value: 'ka' },
  { name: 'Azerbaijani (azərbaycanca)', value: 'az' },
  { name: 'Kazakh (қазақша)', value: 'kk' },
  { name: 'Uzbek (oʻzbekcha / ўзбекча)', value: 'uz' },
  { name: 'Turkmen (Türkmençe)', value: 'tk' },
  { name: 'Kyrgyz (кыргызча)', value: 'ky' },
  { name: 'Tajik (тоҷикӣ)', value: 'tg' },
  { name: 'Mongolian (монгол)', value: 'mn' },
  { name: 'Burmese (မြန်မာဘာသာ)', value: 'my' },
  { name: 'Khmer (ភាសាខ្មែរ)', value: 'km' },
  { name: 'Lao (ພາສາລາວ)', value: 'lo' },
  { name: 'Sinhala (සිංහල)', value: 'si' },
  { name: 'Tibetan (བོད་ཡིག)', value: 'bo' },
  { name: 'Dzongkha (རྫོང་ཁ)', value: 'dz' },
  { name: 'Nepali (नेपाली)', value: 'ne' },
  { name: 'Pashto (پښتو)', value: 'ps' },
  { name: 'Kurdish (کوردی)', value: 'ku' },
  { name: 'Somali (Soomaaliga)', value: 'so' },
  { name: 'Tigrinya (ትግርኛ)', value: 'ti' },
  { name: 'Oromo (Oromoo)', value: 'om' }
])
let debounceTimer

onMounted(() => {
  selectedWiki.value = 'en' // Default to English
  searchQuery.value = 'English (English)'
})

function handleInput() {
  const query = username.value.trim()
  const lang = selectedWiki.value

  clearTimeout(debounceTimer)

  if (!query || !lang) {
    suggestions.value = []
    return
  }

  debounceTimer = setTimeout(() => {
    fetchSuggestions(lang, query)
  }, 300)
}

async function fetchSuggestions(lang, query) {
  try {
    const url = `https://${lang}.wikipedia.org/w/api.php?action=query&list=allusers&auprefix=${encodeURIComponent(query)}&aulimit=5&format=json&origin=*`

    const response = await fetch(url)
    const data = await response.json()

    if (data.query && data.query.allusers) {
      suggestions.value = data.query.allusers
    } else {
      suggestions.value = []
    }
  } catch (e) {
    console.error('Autocomplete error', e)
    suggestions.value = []
  }
}

function selectSuggestion(name) {
  username.value = name
  suggestions.value = []
  fetchStats()
}

function clearResults() {
  userData.value = null
  error.value = ''
  suggestions.value = []
  username.value = ''
}

function resetInspector() {
  userData.value = null
  error.value = ''
  suggestions.value = []
  username.value = ''
  selectedWiki.value = 'en'
  searchQuery.value = 'English (English)'
}

async function fetchStats() {
  const lang = selectedWiki.value
  const user = username.value.trim()

  suggestions.value = []
  userData.value = null
  error.value = ''

  if (!user) {
    error.value = 'Please enter a username.'
    return
  }

  loading.value = true

  try {
    const apiUrl = `https://${lang}.wikipedia.org/w/api.php?action=query&list=users&ususers=${encodeURIComponent(user)}&usprop=blockinfo|groups|editcount|registration|gender&format=json&origin=*`

    const response = await fetch(apiUrl)
    const data = await response.json()

    loading.value = false

    if (data.query && data.query.users && data.query.users[0]) {
      const userInfo = data.query.users[0]
      if (userInfo.missing !== undefined) {
        error.value = `User "${user}" not found.`
      } else if (userInfo.invalid !== undefined) {
        error.value = 'Invalid username format.'
      } else {
        userData.value = userInfo
      }
    } else {
      error.value = 'User not found.'
    }
  } catch (e) {
    loading.value = false
    error.value = 'Connection error.'
  }
}

function formatRegistrationDate(registration) {
  if (!registration) return 'Pre-2005 / Unknown'
  return new Date(registration).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function filterLanguages() {
  // Filtering is handled by computed property
}

function selectWiki(wiki) {
  selectedWiki.value = wiki.value
  searchQuery.value = wiki.name
  showDropdown.value = false
  clearResults()
}

function hideDropdown() {
  setTimeout(() => {
    showDropdown.value = false
  }, 150) // Delay to allow click on dropdown item
}
</script>

<style scoped>
.inspector-container {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: 100%;
}

.inspector-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 1.5rem 0;
}

.form-section {
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
  position: relative;
}

label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  box-sizing: border-box;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 2px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
  margin-top: -2px;
}

.suggestion-item {
  padding: 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
  transition: background 0.2s;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background-color: #f9fafb;
  color: #667eea;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 2px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
  margin-top: -2px;
}

.dropdown-item {
  padding: 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
  transition: background 0.2s;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background-color: #f9fafb;
  color: #667eea;
}

.button-group {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.validate-btn {
  flex: 1;
  padding: 0.875rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.validate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.validate-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
}

.reset-btn {
  padding: 0.875rem 1rem;
  background: white;
  color: #6b7280;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.reset-btn:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-1px);
}

.reset-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.loader-message {
  text-align: center;
  margin-top: 1rem;
  color: #6b7280;
  font-size: 0.875rem;
  font-style: italic;
}

.error-message {
  color: #ef4444;
  text-align: center;
  margin-top: 1rem;
  font-weight: 600;
  font-size: 0.875rem;
  padding: 0.75rem;
  background: #fef2f2;
  border-radius: 6px;
  border: 1px solid #fecaca;
}

.user-results {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid #f3f4f6;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
}

.user-name {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  background: #f9fafb;
  padding: 0.875rem;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
}

.status-active {
  color: #10b981 !important;
}

.status-blocked {
  color: #ef4444 !important;
}

.groups-section {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
}

.groups-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.75rem;
}

.groups-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.group-badge {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.no-groups {
  color: #9ca3af;
  font-size: 0.875rem;
  font-style: italic;
}
</style>
