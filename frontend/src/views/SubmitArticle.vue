<template>
  <div class="submit-article-page">
    <!-- Step 1: Search -->
    <div v-if="step === 1" class="step-container compact">
      <div class="modal-header">
        <h2 class="page-title">{{ editathon.name || 'Loading...' }}</h2>
        <button class="close-btn" @click="goBackToDashboard">✕</button>
      </div>
      
      <div class="search-content">
        <div class="search-card">
          <div class="search-title-row">
            <h3 class="search-title">Article's title</h3>
          </div>
          <div class="search-container condensed">
            <input 
              type="text" 
              v-model="articleTitle"
              @input="searchWikipediaArticles"
              placeholder="Search article titles"
              autocomplete="off"
              class="search-input"
            >
            <div v-if="searchingArticles" class="loading-indicator">
              Searching...
            </div>
            <div v-if="articleSuggestions.length > 0" class="suggestions-dropdown">
              <div
                v-for="(suggestion, index) in articleSuggestions"
                :key="index"
                class="suggestion-item"
                @click="selectArticleSuggestion(suggestion)"
              >
                <div class="suggestion-title">
                  {{ suggestion.title }}
                  <span class="lang-badge">{{ suggestion.language.toUpperCase() }}</span>
                </div>
                <div v-if="suggestion.description" class="suggestion-description">
                  {{ suggestion.description }}
                </div>
              </div>
            </div>
            <div v-if="articleTitle.length > 2 && !searchingArticles && articleSuggestions.length === 0 && hasSearched && !selectedArticle" class="no-results">
              No articles found. Try different keywords.
            </div>
          </div>
          
          <div class="action-buttons compact">
            <button class="btn btn-secondary ghost" @click="goBackToDashboard">Cancel</button>
            <button 
              class="btn btn-submit" 
              @click="goToStep2"
              :disabled="!selectedArticle"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 2: Preview & Submit -->
    <div v-if="step === 2" class="step-container full-height">
      <div class="modal-header">
        <h2 class="page-title">{{ editathon.name || 'Loading...' }}</h2>
        <button class="close-btn" @click="goBackToDashboard">✕</button>
      </div>

      <div class="submit-layout">
        <!-- Article Viewer Side (Left) -->
        <div class="article-viewer">
           <div v-if="loading" class="loading-state">
             <div class="spinner"></div>
             <p>Loading article content...</p>
           </div>
           <div v-else-if="articleContent" class="article-content-scroll" v-html="articleContent"></div>
           <div v-else class="error-state">
             <p>Failed to load article content.</p>
           </div>
        </div>

        <!-- Metadata Side (Right) -->
        <div class="review-sidebar">
          <h3 class="article-heading">{{ articleTitle }}</h3>
          
          <div class="metadata-box">
            <div class="metadata-item success">
              <span class="icon">✅</span> 
              <span>Created at {{ formatDateTime(articleStats.createdAt) }}</span>
            </div>
            
            <div class="metadata-item success">
              <span class="icon">✅</span> 
              <span v-if="wikiLanguage">Language: {{ wikiLanguage.toUpperCase() }} wiki</span>
              <span v-else>Is in the main namespace</span>
            </div>

            <div class="metadata-item success">
              <span class="icon">✅</span>
              <span>Is in the main namespace</span>
            </div>

            <div v-if="unmetRules.length" class="metadata-item warning">
              <span class="icon">⚠️</span>
              <span>
                This article does not meet:
                <ul class="rule-list">
                  <li v-for="(rule, idx) in unmetRules" :key="idx">{{ rule }}</li>
                </ul>
              </span>
            </div>

            <div class="stats-box">
              <p><strong>Size:</strong> {{ articleStats.bytes ? `${articleStats.bytes} bytes` : 'Unknown' }}</p>
              <p><strong>Words:</strong> {{ articleStats.words ? `${articleStats.words} words` : 'Unknown' }}</p>
              <p><strong>Created by:</strong> {{ articleStats.createdBy || 'Unknown' }}</p>
            </div>
          </div>
          
          <div class="sidebar-footer">
            <button class="btn btn-secondary" @click="step = 1">Back</button>
            <button class="btn btn-submit primary-action" @click="addArticle" :disabled="unmetRules.length > 0">Add</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchEditathonDashboard, findArticleWithFallback } from '../services/api'
import { store } from '../store'

const route = useRoute()
const router = useRouter()

const editathonId = ref(null)
const editathon = ref({})
const wikiLanguage = ref('en')
const step = ref(1)

// Form data
const articleTitle = ref('')
const articleContent = ref('')
const loading = ref(false)
const articleSuggestions = ref([])
const searchingArticles = ref(false)
const hasSearched = ref(false)
const selectedArticle = ref(null)
const articleStats = ref({
  createdAt: null,
  bytes: null,
  words: null,
  createdBy: null
})
const unmetRules = ref([])
let searchTimeout = null

// Methods
function goBackToDashboard() {
  router.push(`/editathon/${editathonId.value}`)
}

function goToStep2() {
  if (!selectedArticle.value) return
  articleTitle.value = selectedArticle.value.title
  step.value = 2
  fetchArticleContent(articleTitle.value)
}

async function fetchArticleContent(title) {
  loading.value = true
  articleContent.value = ''
  articleStats.value = { createdAt: null, bytes: null, words: null, createdBy: null }
  
  try {
    // Use multilingual API to find article in any available language
    const languagePriority = [
      wikiLanguage.value, // Try primary language first
      'en', 'ml', 'es', 'fr', 'de' // Common fallbacks
    ].filter((v, i, a) => a.indexOf(v) === i) // Remove duplicates
    
    const result = await findArticleWithFallback(title, languagePriority, 'wikipedia')
    
    if (result.found) {
      const foundLanguage = result.language
      const foundTitle = result.title
      
      // Fetch the article summary (extract) instead of full content
      const response = await fetch(
        `https://${foundLanguage}.wikipedia.org/w/api.php?action=query&format=json&prop=extracts|pageimages|revisions&exintro=true&pithumbsize=800&piprop=original&rvprop=user|timestamp|size&rvlimit=1&rvdir=newer&titles=${encodeURIComponent(foundTitle)}&origin=*`
      )
      const data = await response.json()
      const pages = data.query.pages
      const pageId = Object.keys(pages)[0]
      
      if (pageId !== '-1' && pages[pageId].extract) {
        const page = pages[pageId]
        const content = page.extract
        const imageUrl = page?.original?.source || page?.thumbnail?.source
        const firstRevision = page?.revisions?.[0]
        const createdAt = firstRevision?.timestamp || null
        const createdBy = firstRevision?.user || null
        const bytes = firstRevision?.size || page?.length || null
        const words = estimateWordCount(content)
        
        // Show language indicator if found in different language
        const langIndicator = foundLanguage !== wikiLanguage.value 
          ? `<div class="language-notice">
               ⚠️ Article not found in ${wikiLanguage.value.toUpperCase()}, showing ${foundLanguage.toUpperCase()} version
             </div>`
          : ''

        const leadImage = imageUrl
          ? `<div class="lead-image">
               <img src="${imageUrl}" alt="${foundTitle}" loading="lazy" />
             </div>`
          : ''
        
        articleContent.value = `
          <div class="wikipedia-article">
            ${langIndicator}
            <div class="wiki-source-header">
              Source: <a href="${result.url}" target="_blank">${foundLanguage.toUpperCase()} Wikipedia</a>
              ${result.totalLanguages > 1 ? ` • Available in ${result.totalLanguages} languages` : ''}
            </div>
            ${leadImage}
            ${content}
          </div>
        `

        articleStats.value = {
          createdAt,
          bytes,
          words,
          createdBy
        }

        evaluateRules()
      } else {
        throw new Error('Failed to load article content')
      }
    } else {
      // Article not found
      articleContent.value = `
        <div class="article-not-found">
          <h3>Article Not Found</h3>
          <p>Could not find Wikipedia article for "<strong>${title}</strong>"</p>
        </div>
      `
    }
  } catch (error) {
    console.error('Error fetching article:', error)
    articleContent.value = `
      <div class="article-error">
        <h3>Error Loading Article</h3>
        <p>${error.message}</p>
      </div>
    `
  } finally {
    loading.value = false
  }
}

function getCurrentDateTime() {
  return new Date().toLocaleString()
}

function formatDateTime(value) {
  if (!value) return 'Unknown'
  const date = new Date(value)
  return isNaN(date.getTime()) ? 'Unknown' : date.toLocaleString()
}

function estimateWordCount(htmlString) {
  if (!htmlString) return null
  const text = htmlString.replace(/<[^>]*>/g, ' ')
  const words = text.trim().split(/\s+/).filter(Boolean)
  return words.length || null
}

function evaluateRules() {
  const rules = editathon.value?.rules || []
  const failures = []
  const stats = articleStats.value || {}
  const bytes = stats.bytes
  const createdAt = stats.createdAt ? new Date(stats.createdAt) : null

  for (const rule of rules) {
    if (!rule || !rule.type) continue
    const type = rule.type
    const cfg = rule.config || {}

    if (type === 'size') {
      if (cfg.min && bytes !== null && bytes < cfg.min) {
        failures.push(`Must be at least ${cfg.min} bytes`)
      }
      if (cfg.hasMax && cfg.max && bytes !== null && bytes > cfg.max) {
        failures.push(`Must be under ${cfg.max} bytes`)
      }
    }

    if (type === 'creation_date') {
      if (createdAt) {
        if (cfg.notBefore) {
          const nb = new Date(cfg.notBefore)
          if (createdAt < nb) failures.push(`Created after ${nb.toLocaleDateString()}`)
        }
        if (cfg.notAfter) {
          const na = new Date(cfg.notAfter)
          if (createdAt > na) failures.push(`Created before ${na.toLocaleDateString()}`)
        }
      }
    }

    if (type === 'namespace') {
      // We assume Wikipedia search returns main namespace articles; only fail if explicitly not main
      if (cfg.namespace && cfg.namespace.toLowerCase() !== 'main') {
        failures.push('Article must be in the main namespace')
      }
    }
  }

  unmetRules.value = failures
}

async function searchWikipediaArticles() {
  const query = articleTitle.value.trim()
  selectedArticle.value = null
  hasSearched.value = false
  
  if (query.length < 2) {
    articleSuggestions.value = []
    return
  }

  if (searchTimeout) clearTimeout(searchTimeout)

  searchTimeout = setTimeout(async () => {
    searchingArticles.value = true
    try {
      // Search in both the editathon language and English (if different)
      const languagesToSearch = new Set([wikiLanguage.value, 'en'])
      const promises = []

      for (const lang of languagesToSearch) {
        const wikiDomain = `${lang}.wikipedia.org`
        promises.push(
          fetch(`https://${wikiDomain}/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=5&namespace=0&format=json&origin=*`)
            .then(res => res.json())
            .then(data => ({ lang, data }))
            .catch(err => ({ lang, error: err }))
        )
      }

      const results = await Promise.all(promises)
      const combinedSuggestions = []

      for (const result of results) {
        if (result.data) {
          const lang = result.lang
          const data = result.data
          // data[1] = titles, data[2] = descriptions, data[3] = urls
          data[1].forEach((title, index) => {
            combinedSuggestions.push({
              title: title,
              description: data[2][index],
              url: data[3][index],
              language: lang
            })
          })
        }
      }
      
      // Remove duplicates (by title + language, though title might be same across langs)
      // Actually, we want to show if it's available in multiple languages?
      // For now, just show all results.
      articleSuggestions.value = combinedSuggestions
    } catch (error) {
      console.error('Error searching Wikipedia:', error)
      articleSuggestions.value = []
    } finally {
      searchingArticles.value = false
      hasSearched.value = true
    }
  }, 300)
}

function selectArticleSuggestion(suggestion) {
  selectedArticle.value = suggestion
  articleTitle.value = suggestion.title
  // Update the wikiLanguage to match the selected article's language
  // This ensures Step 2 fetches from the correct Wikipedia
  wikiLanguage.value = suggestion.language
  articleSuggestions.value = []
  hasSearched.value = false
}

async function addArticle() {
  if (unmetRules.value.length > 0) {
    alert('This article does not meet all eligibility rules. Please choose another article.')
    return
  }
  try {
    const response = await fetch(`http://localhost:5000/api/editathon/${editathonId.value}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'Clintacc',
        article_title: articleTitle.value
      })
    })

    if (response.ok) {
      alert(`Article "${articleTitle.value}" successfully added by Clintacc!`)
      goBackToDashboard()
    } else {
      const error = await response.json()
      alert(`Error: ${error.error}`)
    }
  } catch (error) {
    alert(`Error submitting article: ${error.message}`)
  }
}

onMounted(async () => {
  editathonId.value = route.params.id
  
  try {
    const data = await fetchEditathonDashboard(editathonId.value)
    editathon.value = data.editathon
    wikiLanguage.value = data.editathon?.wiki_language || 'ml'
    
    // Check if editathon has finished
    const isFinished = data.editathon?.status === 'completed' || data.editathon?.status === 'archived'
    const endDate = data.editathon?.end_date || data.editathon?.endDate
    const hasEndDatePassed = endDate && new Date(endDate) < new Date()
    
    if (isFinished || hasEndDatePassed) {
      alert('Cannot submit articles: This editathon has finished')
      router.push(`/editathon/${editathonId.value}`)
      return
    }
    
    // Check if current user is a jury member
    const juries = data.juries || []
    const isJury = store.user && juries.some(jury => jury.username === store.user.username)
    if (isJury) {
      alert('Access denied: Jury members cannot submit articles')
      router.push(`/editathon/${editathonId.value}`)
      return
    }
    
    evaluateRules()
    
    // Check for pre-filled title from query params AFTER loading language
    if (route.query.title) {
      articleTitle.value = route.query.title
      step.value = 2
      fetchArticleContent(articleTitle.value)
    }
  } catch (error) {
    console.error('Error loading editathon:', error)
  }
})
</script>

<style scoped>
.submit-article-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8f9fa;
  font-family: 'Arial', sans-serif;
}

.step-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.step-container.compact .modal-header {
  padding: 10px 20px;
}

.step-container.compact .page-title {
  font-size: 16px;
}

.step-container.full-height {
  height: 100%;
  overflow: hidden;
}

.modal-header {
  padding: 12px 24px;
  border-bottom: 1px solid #eee;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: normal;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #333;
  padding: 3px;
}

.close-btn:hover {
  color: #000;
}

/* Step 1 Styles */
.step-container.compact {
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
}

.search-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 20px 16px 32px;
}


.search-card {
  width: min(1100px, 100%);
  background: white;
  padding: 20px 28px;
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.1);
  border: 1px solid #d7e0f5;
}

.search-title-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  margin-bottom: 10px;
}

.search-title {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
  font-weight: 600;
}

.search-hint {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.search-container {
  position: relative;
  margin-bottom: 16px;
}

.search-container.condensed {
  margin-bottom: 8px;
}

.search-input-wrapper {
  display: flex;
  gap: 10px;
}

.lang-select {
  padding: 12px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #f8f9fa;
  cursor: pointer;
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  border: 1px solid #cbd5f5;
  border-radius: 8px;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.loading-indicator {
  padding: 8px;
  text-align: center;
  color: #666;
  font-size: 13px;
}

.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ccc;
  border-top: none;
  border-radius: 0 0 4px 4px;
  max-height: 300px;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.suggestion-item {
  padding: 8px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.suggestion-item:hover {
  background-color: #f8f9fa;
}

.suggestion-title {
  font-weight: 600;
  color: #0645ad;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.lang-badge {
  font-size: 10px;
  background: #eee;
  color: #666;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 8px;
}

.suggestion-description {
  font-size: 12px;
  color: #666;
}

.no-results {
  padding: 8px;
  text-align: left;
  color: #999;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}

.action-buttons.compact {
  justify-content: space-between;
}

.btn {
  padding: 8px 16px;
  font-size: 14px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
}

.btn-secondary {
  background-color: #f8f9fa;
  border: 1px solid #c8c8c8;
  color: #333;
}

.btn-secondary.ghost {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding-left: 0;
}

.btn-submit {
  background-color: #3366cc;
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Step 2 Styles */
.submit-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.article-viewer {
  background: #f9fafb;
  height: 100%;
  overflow: hidden;
}

.wiki-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.review-sidebar {
  padding: 12px;
  overflow: hidden;
  border-left: 1px solid #eee;
  background: white;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-shadow: -2px 0 10px rgba(0,0,0,0.05);
  z-index: 10;
}

.article-heading {
  font-size: 16px;
  margin-top: 0;
  color: #0645ad;
  margin-bottom: 10px;
  flex-shrink: 0;
  font-weight: 500;
  line-height: 1.2;
}

.metadata-box {
  flex: 0 1 auto;
  overflow-y: auto;
  padding-right: 5px;
  min-height: 0;
  max-height: 70vh;
}

.metadata-item {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 13px;
}

.metadata-item:last-child {
  border-bottom: none;
}

.metadata-item.warning {
  color: #d97706;
}

.metadata-item.success {
  color: #059669;
}

.metadata-item.warning {
  color: #d97706;
  align-items: flex-start;
}

.metadata-item.warning ul.rule-list {
  margin: 4px 0 0 0;
  padding-left: 16px;
  color: #555;
  font-size: 12px;
}

.icon {
  font-size: 16px;
  flex-shrink: 0;
}

.stats-box {
  margin-top: 10px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.stats-box p {
  margin: 5px 0;
  display: flex;
  justify-content: space-between;
  color: #495057;
  font-size: 13px;
}

.stats-box strong {
  color: #212529;
}

.sidebar-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-shrink: 0;
  background: white;
}

.primary-action {
  background-color: #00a699;
}

.primary-action:hover {
  background-color: #008f84;
}

@media (max-width: 768px) {
  .submit-layout {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }
  
  .article-viewer {
    flex: 1;
    min-height: 0; /* Important for scrolling */
  }

  .review-sidebar {
    height: auto;
    max-height: 45vh;
    border-left: none;
    border-top: 1px solid #eee;
    padding: 20px;
    box-shadow: 0 -4px 12px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
  }

  .metadata-box {
    overflow-y: auto;
  }

  .article-heading {
    font-size: 18px;
    margin-bottom: 15px;
  }

  .sidebar-footer {
    margin-top: 15px;
    padding-top: 15px;
  }
  
  .modal-header {
    padding: 15px 20px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .search-card {
    padding: 25px;
    max-width: 100%;
    border-radius: 0;
    box-shadow: none;
  }
  
  .search-content {
    padding: 0;
    align-items: flex-start;
    background: white;
  }
}

/* Article Content Styles */
.article-content-scroll {
  height: 100%;
  overflow-y: auto;
  padding: 2rem;
  background: white;
}

.loading-state, .error-state, .article-not-found, .article-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
  text-align: center;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.language-notice {
  background: #fff3cd;
  color: #856404;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border: 1px solid #ffeeba;
}

.wiki-source-header {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.wiki-source-header a {
  color: #0645ad;
  text-decoration: none;
}

.wiki-source-header a:hover {
  text-decoration: underline;
}

.lead-image {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: center;
}

.lead-image img {
  max-width: 100%;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  object-fit: cover;
}

/* Wikipedia Content Styles */
:deep(.wikipedia-article) {
  font-family: sans-serif;
  line-height: 1.6;
  color: #202122;
}

:deep(.wikipedia-article h1),
:deep(.wikipedia-article h2),
:deep(.wikipedia-article h3) {
  border-bottom: 1px solid #a2a9b1;
  margin-bottom: 0.5em;
  padding-bottom: 0.2em;
  font-weight: normal;
}

:deep(.wikipedia-article p) {
  margin: 0.5em 0 1em 0;
}

:deep(.wikipedia-article a) {
  color: #0645ad;
  text-decoration: none;
}

:deep(.wikipedia-article a:hover) {
  text-decoration: underline;
}

:deep(.wikipedia-article img) {
  max-width: 100%;
  height: auto;
}

:deep(.mw-editsection),
:deep(.mw-empty-elt),
:deep(.noprint) {
  display: none;
}
</style>
