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
import { ref, computed } from 'vue'

const searchQuery = ref('')
const showDropdown = ref(false)
const selectedLanguage = ref(null)

const languages = [
  { code: 'af', name: 'Afrikaans' },
  { code: 'ar', name: 'العربية' },
  { code: 'az', name: 'Azərbaycanca' },
  { code: 'be', name: 'Беларуская' },
  { code: 'bg', name: 'Български' },
  { code: 'bn', name: 'বাংলা' },
  { code: 'br', name: 'Brezhoneg' },
  { code: 'bs', name: 'Bosanski' },
  { code: 'ca', name: 'Català' },
  { code: 'cs', name: 'Čeština' },
  { code: 'cy', name: 'Cymraeg' },
  { code: 'da', name: 'Dansk' },
  { code: 'de', name: 'Deutsch' },
  { code: 'el', name: 'Ελληνικά' },
  { code: 'en', name: 'English' },
  { code: 'eo', name: 'Esperanto' },
  { code: 'es', name: 'Español' },
  { code: 'et', name: 'Eesti' },
  { code: 'eu', name: 'Euskara' },
  { code: 'fa', name: 'فارسی' },
  { code: 'fi', name: 'Suomi' },
  { code: 'fr', name: 'Français' },
  { code: 'fy', name: 'Frysk' },
  { code: 'ga', name: 'Gaeilge' },
  { code: 'gd', name: 'Gàidhlig' },
  { code: 'gl', name: 'Galego' },
  { code: 'gu', name: 'ગુજરાતી' },
  { code: 'he', name: 'עברית' },
  { code: 'hi', name: 'हिन्दी' },
  { code: 'hr', name: 'Hrvatski' },
  { code: 'hu', name: 'Magyar' },
  { code: 'hy', name: 'Հայերեն' },
  { code: 'id', name: 'Bahasa Indonesia' },
  { code: 'is', name: 'Íslenska' },
  { code: 'it', name: 'Italiano' },
  { code: 'ja', name: '日本語' },
  { code: 'jv', name: 'Basa Jawa' },
  { code: 'ka', name: 'ქართული' },
  { code: 'kk', name: 'Қазақша' },
  { code: 'km', name: 'ភាសាខ្មែរ' },
  { code: 'kn', name: 'ಕನ್ನಡ' },
  { code: 'ko', name: '한국어' },
  { code: 'ku', name: 'Kurdî' },
  { code: 'ky', name: 'Кыргызча' },
  { code: 'la', name: 'Latina' },
  { code: 'lb', name: 'Lëtzebuergesch' },
  { code: 'lo', name: 'ລາວ' },
  { code: 'lt', name: 'Lietuvių' },
  { code: 'lv', name: 'Latviešu' },
  { code: 'mg', name: 'Malagasy' },
  { code: 'mi', name: 'Māori' },
  { code: 'mk', name: 'Македонски' },
  { code: 'ml', name: 'മലയാളം' },
  { code: 'mn', name: 'Монгол' },
  { code: 'mr', name: 'मराठी' },
  { code: 'ms', name: 'Bahasa Melayu' },
  { code: 'mt', name: 'Malti' },
  { code: 'my', name: 'မြန်မာဘာသာ' },
  { code: 'nb', name: 'Norsk bokmål' },
  { code: 'ne', name: 'नेपाली' },
  { code: 'nl', name: 'Nederlands' },
  { code: 'nn', name: 'Norsk nynorsk' },
  { code: 'oc', name: 'Occitan' },
  { code: 'or', name: 'ଓଡ଼ିଆ' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ' },
  { code: 'pl', name: 'Polski' },
  { code: 'ps', name: 'پښتو' },
  { code: 'pt', name: 'Português' },
  { code: 'ro', name: 'Română' },
  { code: 'ru', name: 'Русский' },
  { code: 'sd', name: 'سنڌي' },
  { code: 'si', name: 'සිංහල' },
  { code: 'sk', name: 'Slovenčina' },
  { code: 'sl', name: 'Slovenščina' },
  { code: 'sq', name: 'Shqip' },
  { code: 'sr', name: 'Српски / Srpski' },
  { code: 'sv', name: 'Svenska' },
  { code: 'sw', name: 'Kiswahili' },
  { code: 'ta', name: 'தமிழ்' },
  { code: 'te', name: 'తెలుగు' },
  { code: 'tg', name: 'Тоҷикӣ' },
  { code: 'th', name: 'ไทย' },
  { code: 'tk', name: 'Türkmençe' },
  { code: 'tl', name: 'Tagalog' },
  { code: 'tr', name: 'Türkçe' },
  { code: 'tt', name: 'Татарча / Tatarça' },
  { code: 'ug', name: 'ئۇيغۇرچە / Uyghurche' },
  { code: 'uk', name: 'Українська' },
  { code: 'ur', name: 'اردو' },
  { code: 'uz', name: 'Oʻzbekcha / Ўзбекча' },
  { code: 'vi', name: 'Tiếng Việt' },
  { code: 'wo', name: 'Wolof' },
  { code: 'xh', name: 'isiXhosa' },
  { code: 'yi', name: 'ייִדיש' },
  { code: 'yo', name: 'Yorùbá' },
  { code: 'zh', name: '中文' },
  { code: 'zu', name: 'isiZulu' }
]

const filteredLanguages = computed(() => {
  if (searchQuery.value.length < 1) return []
  return languages.filter(language =>
    language.code.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    language.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const displayedLanguages = computed(() => {
  return filteredLanguages.value.slice(0, 4) // Limit to 4 suggestions
})

function filterLanguages() {
  // Triggered on input
}

function selectLanguage(language) {
  selectedLanguage.value = language
  searchQuery.value = `${language.code}: ${language.name}`
  showDropdown.value = false
}

function hideDropdown() {
  setTimeout(() => {
    showDropdown.value = false
  }, 150) // Delay to allow click on dropdown item
}
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
