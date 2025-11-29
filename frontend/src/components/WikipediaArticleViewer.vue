<template>
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Wikipedia Article Viewer</h2>
        <button class="close-btn" @click="closeModal">&times;</button>
      </div>
      <div class="modal-body">
        <div class="search-section">
          <input
            type="text"
            v-model="searchQuery"
            @input="onSearchInput"
            placeholder="Search for an article or topic..."
            class="search-input"
          >
          <div v-if="searchSuggestions.length > 0" class="suggestions-list">
            <div
              v-for="suggestion in searchSuggestions"
              :key="suggestion"
              @click="selectSuggestion(suggestion)"
              class="suggestion-item"
            >
              {{ suggestion }}
            </div>
          </div>
        </div>
        <div v-if="loading" class="loading">
          <p>Loading article...</p>
        </div>
        <div v-else-if="error" class="error">
          <p>{{ error }}</p>
        </div>
        <div v-else-if="articleTitle" class="article-content">
          <h3>{{ articleTitle }}</h3>
          <div v-html="articleContent"></div>
          <div class="article-actions">
            <a :href="wikipediaUrl" target="_blank" class="btn btn-primary">View on Wikipedia</a>
            <button v-if="!articleExists" @click="createOnWikipedia" class="btn btn-warning">Create on Wikipedia</button>
            <button @click="useForSubmission" class="btn btn-secondary">Use for Submission</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  showModal: {
    type: Boolean,
    default: false
  },
  articleTitle: {
    type: String,
    default: ''
  },
  wikiLanguage: {
    type: String,
    default: 'en' // Default to English, can be 'ml' for Malayalam, etc.
  }
})

const emit = defineEmits(['close', 'use-article'])

const articleContent = ref('')
const loading = ref(false)
const error = ref('')
const wikipediaUrl = ref('')
const searchQuery = ref('')
const searchSuggestions = ref([])
const articleExists = ref(true)

const closeModal = () => {
  emit('close')
  // Reset state when closing
  searchQuery.value = ''
  searchSuggestions.value = []
  articleContent.value = ''
  error.value = ''
  articleExists.value = true
}

const useForSubmission = () => {
  emit('use-article', {
    title: props.articleTitle || searchQuery.value,
    content: articleContent.value
  })
  closeModal()
}

const createOnWikipedia = () => {
  const wikiDomain = `${props.wikiLanguage}.wikipedia.org`
  const url = `https://${wikiDomain}/wiki/${encodeURIComponent(props.articleTitle || searchQuery.value)}?action=edit&redlink=1`
  window.open(url, '_blank')
}

const fetchArticle = async (title) => {
  if (!title) return

  loading.value = true
  error.value = ''
  articleExists.value = true

  try {
    // Use Wikipedia API to get article extract (supports multiple languages)
    const wikiDomain = `${props.wikiLanguage}.wikipedia.org`
    const response = await axios.get(`https://${wikiDomain}/api/rest_v1/page/summary/${encodeURIComponent(title)}`)
    articleContent.value = response.data.extract_html || response.data.extract || '<p>No content available</p>'
    wikipediaUrl.value = response.data.content_urls?.desktop?.page || `https://${wikiDomain}/wiki/${encodeURIComponent(title)}`
  } catch (err) {
    console.error('Error fetching article:', err)
    if (err.response && err.response.status === 404) {
      articleExists.value = false
      error.value = `The article "${title}" does not exist on ${props.wikiLanguage.toUpperCase()} Wikipedia. You can create it!`
      articleContent.value = '<p>This article does not exist yet. Consider creating it to contribute to Wikipedia.</p>'
      wikipediaUrl.value = `https://${props.wikiLanguage}.wikipedia.org/wiki/${encodeURIComponent(title)}`
    } else {
      error.value = 'Failed to load article. Please try again.'
      articleContent.value = ''
    }
  } finally {
    loading.value = false
  }
}

const onSearchInput = async () => {
  const query = searchQuery.value.trim()
  if (query.length < 2) {
    searchSuggestions.value = []
    return
  }

  try {
    // Use Wikipedia opensearch API for suggestions (supports multiple languages)
    const wikiDomain = `${props.wikiLanguage}.wikipedia.org`
    const response = await axios.get(`https://${wikiDomain}/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=10&namespace=0&format=json&origin=*`)
    searchSuggestions.value = response.data[1] || []
  } catch (err) {
    console.error('Error fetching suggestions:', err)
    searchSuggestions.value = []
  }
}

const selectSuggestion = (suggestion) => {
  searchQuery.value = suggestion
  searchSuggestions.value = []
  fetchArticle(suggestion)
}

// Watch for changes in articleTitle or showModal
watch(() => props.articleTitle, (newTitle) => {
  if (newTitle && props.showModal) {
    searchQuery.value = newTitle
    fetchArticle(newTitle)
  }
})

watch(() => props.showModal, (newShow) => {
  if (newShow && props.articleTitle) {
    searchQuery.value = props.articleTitle
    fetchArticle(props.articleTitle)
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ddd;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.loading, .error {
  text-align: center;
  padding: 40px;
}

.error {
  color: #dc3545;
}

.article-content {
  line-height: 1.6;
}

.article-content :deep(p) {
  margin-bottom: 1rem;
}

.article-content :deep(h1), .article-content :deep(h2), .article-content :deep(h3) {
  color: #333;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

.article-actions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ddd;
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  text-decoration: none;
  display: inline-block;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}
</style>
