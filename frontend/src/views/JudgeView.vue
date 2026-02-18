<template>
  <div class="judge-page-fullscreen">
    <div class="judge-header">
      <button class="back-btn" @click="goBack">← Back to Dashboard</button>
      <h2>All Articles (Jury View)</h2>
      <div class="jury-names">
        <span v-for="jury in juries" :key="jury.id" class="jury-name-label">{{ jury.username }}</span>
      </div>
    </div>

    <!-- Articles List with Jury Checkboxes -->
    <div class="articles-list-container">
      <div 
        v-for="(article, index) in articles" 
        :key="article.id" 
        class="article-row"
        :class="{ active: currentIndex === index }"
        @click="selectArticle(index)"
      >
        <div class="article-info">
          <span class="article-number">{{ index + 1 }}.</span>
          <a :href="getWikipediaUrl(article.title)" target="_blank" class="article-link" @click.stop>
            {{ article.title }}
          </a>
          <button class="btn-review" @click.stop="openArticleReview(index)" title="Review this article">
            📝
          </button>
        </div>
        <div class="jury-checkboxes-row">
          <div 
            v-for="jury in juries" 
            :key="jury.id" 
            class="jury-checkbox-box"
            :class="{ checked: isReviewedByJury(article.id, jury.username) }"
            @click.stop="toggleJuryMark(article.id, jury.username)"
            :title="jury.username"
          ></div>
        </div>
      </div>
    </div>

    <!-- Footer with Save -->
    <div class="judge-footer">
      <button class="btn btn-primary" @click="saveAllReviews">Save</button>
      <button class="btn btn-secondary" @click="goBack">Close</button>
    </div>

    <!-- Article Review Modal (WikiLite Style) -->
    <div v-if="showReviewModal" class="review-modal-overlay" @click="closeReviewModal">
      <div class="review-modal" @click.stop>
        <button class="close-btn" @click="closeReviewModal">✕</button>
        
        <div class="review-layout">
          <!-- Article Content - Wikipedia iframe embed -->
          <div class="article-viewer">
            <div class="article-header">
              <h2>{{ current?.title }}</h2>
              <div class="article-meta-row">
                <a :href="getWikipediaUrl(current?.title)" target="_blank" class="wiki-link">
                  Open in new tab →
                </a>
              </div>
            </div>
            
            <!-- Embed Wikipedia directly using iframe -->
            <div class="article-content">
              <iframe 
                :src="getWikipediaMobileUrl(current?.title)"
                class="wiki-iframe"
                frameborder="0"
                sandbox="allow-scripts allow-same-origin allow-popups"
              ></iframe>
            </div>
          </div>

          <!-- Review Sidebar -->
          <div class="review-sidebar">
            <div class="user-header">
              <span class="avatar">👤</span>
              <div>
                <div class="user-name">{{ currentUser }}</div>
                <div class="user-role">Reviewing Article</div>
              </div>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <span class="icon">👤</span>
                <span class="label">AUTHOR</span>
                <span class="value">{{ current?.author }}</span>
              </div>
              <div class="info-item">
                <span class="icon">📝</span>
                <span class="label">WORDS</span>
                <span class="value">{{ current?.words }}</span>
              </div>
              <div class="info-item">
                <span class="icon">💾</span>
                <span class="label">BYTES</span>
                <span class="value">{{ current?.bytes }}</span>
              </div>
              <div class="info-item">
                <span class="icon">📅</span>
                <span class="label">ADDED ON</span>
                <span class="value">{{ formatDate(current?.addedOn) }}</span>
              </div>
            </div>

            <div class="review-card">
              <div class="card-section">
                <div class="section-label">✅ Decision</div>
                <div class="decision-buttons">
                  <button class="btn-accept" @click="handleVote('accept')">✓ Accept</button>
                  <button class="btn-reject" @click="handleVote('reject')">✕ Reject</button>
                </div>
              </div>

              <div class="card-section">
                <div class="section-label">💬 Comment</div>
                <textarea v-model="judgeComment" placeholder="Add your review comments..."></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchEditathon } from '../services/api'
import { store } from '../store'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const articles = ref([])
const currentIndex = ref(0)
const fullArticleHtml = ref('')
const isLoadingArticle = ref(false)
const currentUser = 'Clintacc'
const judgeComment = ref('')
const wikiLanguage = ref('en')
const showReviewModal = ref(false)
const juries = ref([
  { id: 1, username: 'Narutolovehinata5' },
  { id: 2, username: 'ZI Jony' }
])

// WikiLite-style search functionality
const searchQuery = ref('')
const searchSuggestions = ref([])
const articleWordCount = ref(0)
const articleTimestamp = ref('')
let searchTimeout = null

// Get editathon ID from route params
const editId = computed(() => route.params.id)

const current = computed(() => {
  return articles.value[currentIndex.value] || null
})

onMounted(async () => {
  console.log('JudgeView mounted, editId:', editId.value)
  const data = await fetchEditathon(editId.value)
  console.log('Fetched data:', data)
  if(!data) return
  
  // Set wiki language from editathon data
  if (data.wiki_language) {
    wikiLanguage.value = data.wiki_language
  } else if (data.editathon?.wiki_language) {
    wikiLanguage.value = data.editathon.wiki_language
  }
  console.log('Wiki language set to:', wikiLanguage.value)
  
  articles.value = (data.articles || []).map(a => ({ 
    ...a, 
    reviewedBy: a.reviewedBy || [], 
    marksBy: a.marksBy || {},
    author: a.author || a.user_name || '—',
    words: a.words || 150,
    bytes: a.bytes || 2500
  }))
  
  if(data.juries && data.juries.length > 0) {
    juries.value = data.juries
  }
  
  // Check if current user is a jury member
  const isJury = store.user && juries.value.some(jury => jury.username === store.user.username)
  if (!isJury) {
    alert('Access denied: Only jury members can judge articles')
    router.push(`/editathon/${editId.value}`)
    return
  }
})

function selectArticle(index) {
  currentIndex.value = index
}

function openArticleReview(index) {
  currentIndex.value = index
  showReviewModal.value = true
  searchQuery.value = ''
  searchSuggestions.value = []
  loadFullArticle(articles.value[index].title)
}

function closeReviewModal() {
  showReviewModal.value = false
  searchSuggestions.value = []
}

// WikiLite-style: Fetch FULL article content using Wikipedia extracts API
async function loadFullArticle(title) {
  if (!title) return
  
  isLoadingArticle.value = true
  fullArticleHtml.value = ''
  articleWordCount.value = 0
  articleTimestamp.value = ''
  
  try {
    // Clean the title - keep spaces, Wikipedia API handles them
    const cleanTitle = title.trim()
    
    console.log('Fetching article:', cleanTitle)
    
    // WikiLite uses action=query&prop=extracts for full article content
    // Using exintro=false to get full content, not just intro
    const extractUrl = `https://${wikiLanguage.value}.wikipedia.org/w/api.php?` + 
      `action=query&prop=extracts&exsectionformat=wiki&titles=${encodeURIComponent(cleanTitle)}` +
      `&redirects=true&format=json&origin=*`
    
    console.log('API URL:', extractUrl)
    
    const response = await axios.get(extractUrl, { timeout: 15000 })
    console.log('API Response:', response.data)
    
    const pages = response.data.query?.pages
    if (pages) {
      const pageId = Object.keys(pages)[0]
      const page = pages[pageId]
      
      console.log('Page ID:', pageId, 'Page:', page)
      
      if (pageId !== '-1' && page && page.extract) {
        // Successfully got content
        fullArticleHtml.value = `
          <div class="wiki-article-body">
            <h2 class="wiki-article-title">${page.title || cleanTitle}</h2>
            ${page.extract}
          </div>
        `
        
        // Estimate word count from content
        const textContent = page.extract.replace(/<[^>]*>/g, '')
        articleWordCount.value = textContent.split(/\s+/).filter(w => w.length > 0).length
        
        // Fetch metadata
        await fetchArticleMetadata(cleanTitle)
      } else if (pageId === '-1' || page?.missing !== undefined) {
        // Article doesn't exist - show helpful message
        fullArticleHtml.value = `
          <div class="article-not-found">
            <h3>📄 Article Not Found</h3>
            <p>The article "<strong>${cleanTitle}</strong>" does not exist on ${wikiLanguage.value.toUpperCase()} Wikipedia yet, or the title may be incorrect.</p>
            <p>You can <a href="https://${wikiLanguage.value}.wikipedia.org/wiki/${encodeURIComponent(cleanTitle)}" target="_blank">view or create it on Wikipedia</a>.</p>
          </div>
        `
      } else {
        fullArticleHtml.value = '<p><em>No content available for this article.</em></p>'
      }
    } else {
      throw new Error('Invalid API response')
    }
    
  } catch (error) {
    console.error('Error fetching full article:', error)
    
    // Fallback: Try using the REST API summary endpoint
    try {
      console.log('Trying REST API fallback...')
      const restUrl = `https://${wikiLanguage.value}.wikipedia.org/api/rest_v1/page/html/${encodeURIComponent(title.trim())}`
      const restResponse = await axios.get(restUrl, { timeout: 10000 })
      
      if (restResponse.data) {
        fullArticleHtml.value = `
          <div class="wiki-article-body wiki-html-content">
            ${restResponse.data}
          </div>
        `
        return
      }
    } catch (restError) {
      console.error('REST API also failed:', restError)
    }
    
    fullArticleHtml.value = `
      <div class="article-error">
        <h3>⚠️ Error Loading Article</h3>
        <p>Could not load the article "<strong>${title}</strong>".</p>
        <p>Please <a href="${getWikipediaUrl(title)}" target="_blank">view on Wikipedia directly</a>.</p>
        <button class="retry-btn" onclick="location.reload()">Retry</button>
      </div>
    `
  } finally {
    isLoadingArticle.value = false
  }
}

// Fetch article metadata (last modified, etc.)
async function fetchArticleMetadata(title) {
  try {
    const metaUrl = `https://${wikiLanguage.value}.wikipedia.org/w/api.php?` +
      `action=query&prop=revisions&rvprop=timestamp&titles=${encodeURIComponent(title)}` +
      `&format=json&origin=*`
    
    const response = await axios.get(metaUrl, { timeout: 5000 })
    const pages = response.data.query?.pages
    if (pages) {
      const pageId = Object.keys(pages)[0]
      const page = pages[pageId]
      if (page.revisions && page.revisions[0]) {
        const timestamp = page.revisions[0].timestamp
        articleTimestamp.value = new Date(timestamp).toLocaleDateString()
      }
    }
  } catch (error) {
    console.log('Could not fetch metadata:', error)
  }
}

// WikiLite-style: Search with autocomplete (opensearch API)
function onSearchInput() {
  // Throttle search requests (like WikiLite's throttle function)
  if (searchTimeout) clearTimeout(searchTimeout)
  
  searchTimeout = setTimeout(async () => {
    const query = searchQuery.value.trim()
    if (query.length < 2) {
      searchSuggestions.value = []
      return
    }
    
    try {
      // WikiLite uses opensearch API
      const searchUrl = `https://${wikiLanguage.value}.wikipedia.org/w/api.php?` +
        `action=opensearch&search=${encodeURIComponent(query)}&limit=8&namespace=0&format=json&origin=*`
      
      const response = await axios.get(searchUrl, { timeout: 5000 })
      
      // opensearch returns: [query, [titles], [descriptions], [urls]]
      if (response.data && response.data[1]) {
        searchSuggestions.value = response.data[1].map((title, i) => ({
          title: title,
          description: response.data[2]?.[i] || '',
          url: response.data[3]?.[i] || ''
        }))
      }
    } catch (error) {
      console.error('Search error:', error)
      searchSuggestions.value = []
    }
  }, 400) // 400ms delay like WikiLite
}

// Select suggestion and load full article
function selectSuggestion(suggestion) {
  searchQuery.value = suggestion.title
  searchSuggestions.value = []
  loadFullArticle(suggestion.title)
}

// WikiLite-style: Full text search
async function searchWikipedia() {
  const query = searchQuery.value.trim()
  if (!query) return
  
  searchSuggestions.value = []
  isLoadingArticle.value = true
  
  try {
    // WikiLite uses action=query&list=search for text search
    const searchUrl = `https://${wikiLanguage.value}.wikipedia.org/w/api.php?` +
      `action=query&list=search&srsearch=${encodeURIComponent(query)}&srwhat=text&srlimit=1&format=json&origin=*`
    
    const response = await axios.get(searchUrl, { timeout: 5000 })
    
    if (response.data.query?.search?.length > 0) {
      const firstResult = response.data.query.search[0]
      loadFullArticle(firstResult.title)
    } else {
      fullArticleHtml.value = `
        <div class="no-results">
          <h3>No Results Found</h3>
          <p>No Wikipedia articles found for "<strong>${query}</strong>".</p>
        </div>
      `
      isLoadingArticle.value = false
    }
  } catch (error) {
    console.error('Search error:', error)
    fullArticleHtml.value = '<p><em>Search failed. Please try again.</em></p>'
    isLoadingArticle.value = false
  }
}

function goBack() {
  router.push(`/editathon/${editId.value}`)
}

function handleVote(action) {
  console.log(`Article: ${current.value.title}, Decision: ${action}, Comment: ${judgeComment.value}`)
  alert(`Vote saved: ${action}`)
  judgeComment.value = ''
  closeReviewModal()
}

function saveAllReviews() {
  console.log('Saving all reviews:', articles.value.map(a => ({ id: a.id, title: a.title, reviewedBy: a.reviewedBy })))
  alert('All reviews saved!')
}

function formatDate(dateString) {
  if(!dateString) return '—'
  try {
    return new Date(dateString).toLocaleDateString()
  } catch {
    return dateString
  }
}

function getWikipediaUrl(title) {
  if(!title) return '#'
  return `https://${wikiLanguage.value}.wikipedia.org/wiki/${encodeURIComponent(title.trim())}`
}

function getWikipediaMobileUrl(title) {
  if(!title) return ''
  return `https://${wikiLanguage.value}.m.wikipedia.org/wiki/${encodeURIComponent(title.trim())}`
}

function isReviewedByJury(articleId, juryUsername) {
  const article = articles.value.find(a => a.id === articleId)
  if(!article) return false
  return article.reviewedBy?.includes(juryUsername)
}

function toggleJuryMark(articleId, juryUsername) {
  const article = articles.value.find(a => a.id === articleId)
  if(!article) return
  
  if(!article.reviewedBy) {
    article.reviewedBy = []
  }
  
  const idx = article.reviewedBy.indexOf(juryUsername)
  if(idx >= 0) {
    article.reviewedBy.splice(idx, 1)
  } else {
    article.reviewedBy.push(juryUsername)
  }
}
</script>

<style scoped>
.judge-page-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
  overflow: hidden;
}

.judge-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: white;
  border-bottom: 1px solid #ddd;
}

.judge-header h2 {
  margin: 0;
  font-size: 1.3rem;
}

.back-btn {
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  color: #0066cc;
}

.back-btn:hover {
  background: #e9ecef;
}

.jury-names {
  display: flex;
  gap: 1rem;
}

.jury-name-label {
  font-size: 0.85rem;
  color: #666;
  padding: 0.25rem 0.5rem;
  background: #f0f0f0;
  border-radius: 4px;
}

.articles-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.article-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: white;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.article-row:hover {
  background: #f5f5f5;
}

.article-row.active {
  background: #e3f2fd;
  border-left: 3px solid #2196f3;
}

.article-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.article-number {
  color: #888;
  font-size: 0.9rem;
  min-width: 25px;
}

.article-link {
  color: #0066cc;
  text-decoration: none;
  flex: 1;
}

.article-link:hover {
  text-decoration: underline;
}

.btn-review {
  padding: 0.25rem 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  opacity: 0.7;
}

.btn-review:hover {
  opacity: 1;
}

.jury-checkboxes-row {
  display: flex;
  gap: 1rem;
}

.jury-checkbox-box {
  width: 20px;
  height: 20px;
  border: 2px solid #ccc;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
}

.jury-checkbox-box:hover {
  border-color: #28a745;
}

.jury-checkbox-box.checked {
  background: #28a745;
  border-color: #28a745;
}

.judge-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: white;
  border-top: 1px solid #ddd;
}

.btn {
  padding: 0.5rem 1.25rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: #0066cc;
  color: white;
  border: none;
}

.btn-secondary {
  background: #f8f9fa;
  border: 1px solid #ddd;
}

/* Review Modal */
.review-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.review-modal {
  background: white;
  width: 95%;
  max-width: 1200px;
  height: 90vh;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  z-index: 10;
}

.review-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.article-viewer {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #ddd;
}

.article-header {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.article-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
}

.wiki-link {
  color: #0066cc;
  text-decoration: none;
  font-size: 0.9rem;
}

.article-content {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

/* Wikipedia iframe embed */
.wiki-iframe {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 200px);
  border: none;
  background: white;
}

.review-sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.6rem;
  background: #f9f9f9;
  border-bottom: 1px solid #eee;
}

.avatar {
  font-size: 1.3rem;
}

.user-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.user-role {
  font-size: 0.7rem;
  color: #888;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  padding: 0.5rem 0.3rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  text-align: center;
  transition: all 0.2s;
}

.info-item:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.info-item .icon {
  font-size: 1rem;
  line-height: 1;
}

.info-item .label {
  font-size: 0.55rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
  line-height: 1;
}

.info-item .value {
  font-weight: 700;
  font-size: 0.75rem;
  color: #111827;
  line-height: 1.2;
  word-break: break-word;
}

.review-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.card-section {
  padding: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.card-section:last-child {
  border-bottom: none;
}

.section-label {
  font-weight: 600;
  font-size: 0.7rem;
  margin-bottom: 0.4rem;
  color: #333;
}

.decision-buttons {
  display: flex;
  gap: 0.3rem;
}

.btn-accept, .btn-reject {
  flex: 1;
  padding: 0.35rem 0.3rem;
  border: 2px solid;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.7rem;
}

.btn-accept {
  border-color: #28a745;
  background: #e8f5e9;
  color: #28a745;
}

.btn-accept:hover {
  background: #28a745;
  color: white;
}

.btn-reject {
  border-color: #dc3545;
  background: #ffebee;
  color: #dc3545;
}

.btn-reject:hover {
  background: #dc3545;
  color: white;
}

.card-section textarea {
  width: 100%;
  min-height: 40px;
  padding: 0.4rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
  font-family: inherit;
  font-size: 0.7rem;
}

/* WikiLite-style Search Box */
.wiki-search-box {
  position: relative;
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}

.wiki-search-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid #c8c8c8;
  border-radius: 3px;
  font-size: 0.95rem;
  transition: all 0.2s linear;
}

.wiki-search-input:focus {
  border-color: #4386F4;
  box-shadow: 0.45em 0 0 #347bff inset;
  outline: none;
}

.wiki-search-btn {
  padding: 0.6rem 1.25rem;
  background: #2196f3;
  border: 1px solid #347bff;
  color: white;
  font-weight: bold;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s ease;
}

.wiki-search-btn:hover {
  box-shadow: 0 1px rgba(0, 0, 0, 0.1), 0 -3px rgba(0, 0, 0, 0.2) inset;
}

/* WikiLite-style Suggestions Dropdown */
.wiki-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 80px;
  background: white;
  border: 1px solid #ccc;
  border-top: none;
  max-height: 300px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.wiki-suggestion-item {
  padding: 0.6rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  transition: background 0.15s;
}

.wiki-suggestion-item:hover {
  background: #FFFDD5;
}

.suggestion-title {
  display: block;
  font-weight: 500;
  color: #0066cc;
}

.suggestion-desc {
  display: block;
  font-size: 0.8rem;
  color: #666;
  margin-top: 0.2rem;
}

/* Article Meta Row */
.article-meta-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-top: 0.5rem;
}

.meta-stat {
  font-size: 0.85rem;
  color: #0B9A13;
}

/* Loading Spinner */
.article-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* WikiLite-style Full Article Content */
.wiki-article-content {
  font-family: sans-serif;
  line-height: 1.7;
}

.wiki-article-content h2 {
  font-size: 1.8rem;
  border-bottom: 1px solid #ccc;
  margin: 1.5rem 0 0.75rem;
  padding-bottom: 0.5rem;
  font-weight: bold;
}

.wiki-article-content h3 {
  font-size: 1.4rem;
  margin: 1.25rem 0 0.5rem;
}

.wiki-article-content h4 {
  font-size: 1.2rem;
  margin: 1rem 0 0.5rem;
}

.wiki-article-content p {
  font-size: 1rem;
  line-height: 1.75;
  text-align: justify;
  color: #333;
  margin: 0.75rem 0;
}

.wiki-article-content ul, .wiki-article-content ol {
  margin: 0.75rem 0 0.75rem 2rem;
}

.wiki-article-content li {
  margin: 0.4rem 0;
  line-height: 1.6;
}

.wiki-article-content a {
  color: #0017FF;
  text-decoration: none;
}

.wiki-article-content a:hover {
  text-decoration: underline;
}

/* Article Not Found / Error States */
.article-not-found, .article-error, .no-results {
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.article-not-found h3, .article-error h3, .no-results h3 {
  color: #dc3545;
  margin-bottom: 1rem;
}

.article-not-found a, .article-error a {
  color: #0066cc;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* Wiki Article Body - Full content display */
.wiki-article-body {
  padding: 0 0.5rem;
}

.wiki-article-title {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
  border-bottom: 1px solid #a2a9b1;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

/* Wiki HTML Content from REST API */
.wiki-html-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Lato, Helvetica, Arial, sans-serif;
}

.wiki-html-content section {
  margin-bottom: 1rem;
}

.wiki-html-content figure {
  margin: 1rem 0;
  text-align: center;
}

.wiki-html-content img {
  max-width: 100%;
  height: auto;
}

.wiki-html-content table {
  border-collapse: collapse;
  margin: 1rem 0;
  width: 100%;
}

.wiki-html-content th, .wiki-html-content td {
  border: 1px solid #a2a9b1;
  padding: 0.5rem;
  text-align: left;
}

.wiki-html-content th {
  background: #eaecf0;
}

.wiki-html-content .infobox {
  float: right;
  clear: right;
  margin: 0 0 1rem 1rem;
  width: 300px;
  font-size: 0.9rem;
  background: #f8f9fa;
  border: 1px solid #a2a9b1;
}

.wiki-html-content .mw-editsection {
  display: none;
}

@media (max-width: 768px) {
  .review-layout {
    flex-direction: column;
  }
  
  .review-sidebar {
    width: 100%;
  }
  
  .wiki-search-box {
    flex-direction: column;
  }
  
  .wiki-suggestions {
    right: 0;
  }
  
  .wiki-html-content .infobox {
    float: none;
    width: 100%;
    margin: 1rem 0;
  }
}
</style>
