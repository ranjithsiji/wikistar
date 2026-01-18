<template>
  <div class="article-review-fullscreen">
    <!-- Header -->
    <div class="review-header">
      <button class="toggle-articles-btn" @click="showArticlesSidebar = !showArticlesSidebar">
        📄 Articles
      </button>
      <h2 class="header-title">{{ currentArticle?.title }}</h2>
      <div class="header-nav">
        <button 
          class="nav-arrow-btn" 
          @click="previousArticle"
          :disabled="currentArticleIndex === 0"
          title="Previous article"
        >
          ◀ Prev
        </button>
        <span class="article-counter">{{ currentArticleIndex + 1 }} / {{ allArticles.length }}</span>
        <button 
          class="nav-arrow-btn" 
          @click="nextArticle"
          :disabled="currentArticleIndex === allArticles.length - 1"
          title="Next article"
        >
          Next ▶
        </button>
      </div>
      <button class="back-btn" @click="goBack">← Back</button>
    </div>

    <!-- Main Content -->
    <div class="review-content">
      <!-- Articles Sidebar (Toggle) - Left Side -->
      <div v-if="showArticlesSidebar" class="articles-sidebar">
        <div class="sidebar-header">
          <h3>Articles ({{ allArticles.length }})</h3>
          <button class="close-sidebar" @click="showArticlesSidebar = false">✕</button>
        </div>
        <div class="articles-list">
          <button 
            v-for="(article, index) in allArticles" 
            :key="article.id"
            class="article-item"
            :class="{ active: currentArticleIndex === index }"
            @click="navigateToArticle(index)"
          >
            <span class="article-num">{{ index + 1 }}</span>
            <span class="article-title">{{ article.title }}</span>
          </button>
        </div>
      </div>

      <!-- Left/Center: Article Viewer -->
      <div class="article-viewer">
        <div class="article-container">
          <div v-if="loading" class="loading">Loading article...</div>
          <div v-else-if="articleContent" class="article-content" v-html="articleContent"></div>
          <div v-else class="error">Failed to load article content</div>
        </div>
      </div>

      <!-- Right: Review Sidebar -->
      <div class="review-sidebar">
        <!-- Jury Reviews Button - Top -->
        <button class="btn-view-jury-reviews" @click="goToJuryReviews">
          📋 Jury Review
        </button>

        <!-- Article Metadata -->
        <div class="article-metadata">
          <div class="metadata-item">
            <span class="metadata-icon">👤</span>
            <span class="metadata-label">Author</span>
            <span class="metadata-value">{{ currentArticle?.author || 'N/A' }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-icon">📝</span>
            <span class="metadata-label">Words</span>
            <span class="metadata-value">{{ currentArticle?.words || 0 }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-icon">💾</span>
            <span class="metadata-label">Bytes</span>
            <span class="metadata-value">{{ currentArticle?.bytes || 0 }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-icon">📅</span>
            <span class="metadata-label">Added On</span>
            <span class="metadata-value">{{ currentArticle?.addedDate || 'N/A' }}</span>
          </div>
        </div>

        <!-- Review Decision Section -->
        <div class="review-decision-box">
          <div class="box-title">✅ Review Decision</div>
          <div class="decision-buttons">
            <button 
              class="decision-btn accept"
              :class="{ active: reviewDecision === 'accept' }"
              @click="reviewDecision = 'accept'"
            >
              <span class="btn-icon">✓</span>
              Accept
            </button>
            <button 
              class="decision-btn reject"
              :class="{ active: reviewDecision === 'reject' }"
              @click="reviewDecision = 'reject'"
            >
              <span class="btn-icon">✕</span>
              Reject
            </button>
          </div>
        </div>

        <!-- Comment Box -->
        <div class="comment-box">
          <div class="box-title">💬 Comment</div>
          <textarea 
            v-model="reviewComment" 
            class="comment-textarea"
            placeholder="Add review comments..."
          ></textarea>
        </div>

        <!-- Footer Actions -->
        <div class="sidebar-footer">
          <button class="btn btn-secondary" @click="goBack">Cancel</button>
          <button class="btn btn-submit" @click="saveReview">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { findArticleWithFallback } from '../services/api'

const router = useRouter()
const route = useRoute()

const currentArticle = ref(null)
const allArticles = ref([])
const currentArticleIndex = ref(0)
const juries = ref([])
const reviewStatus = ref({})
const reviewComment = ref('')
const reviewDecision = ref(null) // 'accept' or 'reject'
const showArticlesSidebar = ref(false)
const articleContent = ref('')
const loading = ref(false)
const wikiLanguage = ref('en') // Default to English

onMounted(() => {
  loadData()
})

function loadData() {
  const editathonId = route.params.id
  
  // Fetch editathon data from backend
  fetch(`http://localhost:5000/api/editathon/${editathonId}`)
    .then(response => response.json())
    .then(data => {
      // Load wiki language from editathon
      wikiLanguage.value = data.editathon?.wiki_language || 'en'
      console.log(`Wiki language: ${wikiLanguage.value}`)
      
      // Load juries from editathon
      juries.value = data.juries || []

      // Load articles from editathon leaderboard
      const articlesMap = {}
      if (data.leaderboard) {
        data.leaderboard.forEach((user) => {
          if (user.articles) {
            user.articles.forEach((article) => {
              const key = article.title
              if (!articlesMap[key]) {
                articlesMap[key] = {
                  id: Object.keys(articlesMap).length + 1,
                  title: article.title,
                  author: article.author,
                  words: article.words || 150,
                  bytes: article.bytes || 2500,
                  addedDate: article.addedOn || new Date().toISOString()
                }
              }
            })
          }
        })
      }

      allArticles.value = Object.values(articlesMap)

      // Find current article from route params
      const articleTitle = route.query.title
      let foundIndex = 0
      if (articleTitle) {
        foundIndex = allArticles.value.findIndex(a => a.title === articleTitle)
      }

      if (allArticles.value.length > 0) {
        currentArticle.value = allArticles.value[foundIndex]
        currentArticleIndex.value = foundIndex
        fetchArticleContent(currentArticle.value.title)
      }

      // Initialize review status
      allArticles.value.forEach(article => {
        reviewStatus.value[article.id] = {}
        juries.value.forEach(jury => {
          reviewStatus.value[article.id][jury.id] = false
        })
      })
    })
    .catch(error => {
      console.error('Error loading editathon data:', error)
      // Fallback to empty
      juries.value = []
      allArticles.value = []
    })
}

function getWikipediaUrl(title) {
  return `https://en.wikipedia.org/wiki/${encodeURIComponent(title)}`
}

function isArticleReviewedBy(article, jury) {
  if (!article) return false
  return reviewStatus.value[article.id]?.[jury.id] || false
}

function toggleReview(article, jury) {
  if (!article) return
  if (!reviewStatus.value[article.id]) {
    reviewStatus.value[article.id] = {}
  }
  reviewStatus.value[article.id][jury.id] = !reviewStatus.value[article.id][jury.id]
}

function saveReview() {
  console.log('Saving review for:', currentArticle.value?.title)
  console.log('Review decision:', reviewDecision.value)
  console.log('Review status:', reviewStatus.value)
  console.log('Comment:', reviewComment.value)
  goBack()
}

function previousArticle() {
  if (currentArticleIndex.value > 0) {
    navigateToArticle(currentArticleIndex.value - 1)
  }
}

function nextArticle() {
  if (currentArticleIndex.value < allArticles.value.length - 1) {
    navigateToArticle(currentArticleIndex.value + 1)
  }
}

function navigateToArticle(index) {
  const article = allArticles.value[index]
  if (article) {
    currentArticle.value = article
    currentArticleIndex.value = index
    showArticlesSidebar.value = false
    // Reset review comment and decision when switching articles
    reviewComment.value = ''
    reviewDecision.value = null
    // Fetch the new article content
    fetchArticleContent(article.title)
  }
}

async function fetchArticleContent(title) {
  loading.value = true
  
  try {
    // Use multilingual API to find article in any available language
    const languagePriority = [
      wikiLanguage.value, // Try primary language first
      'en', 'ml', 'es', 'fr', 'de' // Common fallbacks
    ].filter((v, i, a) => a.indexOf(v) === i) // Remove duplicates
    
    console.log(`Searching article "${title}" with language priority:`, languagePriority)
    
    const result = await findArticleWithFallback(title, languagePriority, 'wikipedia')
    
    if (result.found) {
      const foundLanguage = result.language
      const foundTitle = result.title
      
      console.log(`✓ Article found in ${foundLanguage}: "${foundTitle}"`)
      console.log(`Available in ${result.totalLanguages} languages total`)
      
      // Fetch the actual article content
      const response = await fetch(
        `https://${foundLanguage}.wikipedia.org/w/api.php?action=parse&format=json&page=${encodeURIComponent(foundTitle)}&prop=text&origin=*`
      )
      const data = await response.json()
      
      if (data.parse && data.parse.text && data.parse.text['*']) {
        const content = data.parse.text['*']
        currentArticle.value.title = foundTitle
        
        // Show language indicator if found in different language
        const langIndicator = foundLanguage !== wikiLanguage.value 
          ? `<div style="background: #fff3cd; padding: 0.75rem; border-radius: 4px; margin-bottom: 1rem; color: #856404;">
               ⚠️ Article not found in ${wikiLanguage.value.toUpperCase()}, showing ${foundLanguage.toUpperCase()} version
             </div>`
          : ''
        
        articleContent.value = `
          <div class="wikipedia-article">
            ${langIndicator}
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #ddd;">
              Source: <a href="${result.url}" target="_blank">${foundLanguage.toUpperCase()} Wikipedia</a>
              ${result.totalLanguages > 1 ? ` • Available in ${result.totalLanguages} languages` : ''}
            </div>
            ${content}
          </div>
        `
        console.log(`Article content loaded successfully from ${foundLanguage} Wikipedia`)
      } else {
        throw new Error('Failed to load article content')
      }
    } else {
      // Article not found in any language
      const searchLinks = languagePriority.slice(0, 3).map(lang => 
        `<a href="https://${lang}.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(title)}" target="_blank">${lang.toUpperCase()} Search</a>`
      ).join(' • ')
      
      articleContent.value = `
        <div style="padding: 2rem; color: #d32f2f; font-family: Arial, sans-serif;">
          <h3>Article Not Found</h3>
          <p>Could not find Wikipedia article for "<strong>${title}</strong>"</p>
          <p>Searched in: ${languagePriority.slice(0, 5).map(l => l.toUpperCase()).join(', ')} Wikipedia</p>
          ${result.errors && result.errors.length > 0 ? `<p style="font-size: 0.85rem; color: #666;">${result.errors[0]}</p>` : ''}
          <p>Please check the article title or try searching manually.</p>
          <p style="margin-top: 1rem;">${searchLinks}</p>
        </div>
      `
    }
  } catch (error) {
    console.error('Error fetching article:', error)
    articleContent.value = `
      <div style="padding: 2rem; color: #d32f2f; font-family: Arial, sans-serif;">
        <h3>Error Loading Article</h3>
        <p>${error.message}</p>
        <p>Check browser console for more details.</p>
      </div>
    `
  } finally {
    loading.value = false
  }
}

function goToJuryReviews() {
  // Navigate to the jury articles review page
  router.push({
    name: 'JuryArticlesFullScreen',
    params: { id: route.params.id }
  })
}

function goBack() {
  // Navigate back to editathon dashboard
  router.push({
    name: 'EditathonDashboard',
    params: { id: route.params.id }
  })
}
</script>

<style scoped>
.article-review-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.review-header {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 1.5rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.back-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0;
  transition: color 0.2s;
  white-space: nowrap;
}

.back-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0;
  transition: color 0.2s;
  white-space: nowrap;
}

.back-btn:hover {
  color: #5568d3;
}

.toggle-articles-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0;
  transition: color 0.2s;
  white-space: nowrap;
}

.toggle-articles-btn:hover {
  color: #5568d3;
}

.header-title {
  margin: 0;
  font-size: 1.1rem;
  color: #1a1a1a;
  font-weight: 600;
  flex: 1;
  padding: 0 1.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #f9f9f9;
}

.nav-arrow-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  padding: 0.5rem 0.75rem;
  transition: color 0.2s;
  white-space: nowrap;
}

.nav-arrow-btn:hover:not(:disabled) {
  color: #5568d3;
}

.nav-arrow-btn:disabled {
  color: #ccc;
  cursor: not-allowed;
}

.article-counter {
  font-size: 0.85rem;
  color: #666;
  font-weight: 600;
  min-width: 50px;
  text-align: center;
}

.review-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #1a1a1a;
  flex: 1;
}

.wiki-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;
  transition: color 0.2s;
}

.wiki-link:hover {
  color: #5568d3;
  text-decoration: underline;
}

.review-content {
  flex: 1;
  display: grid;
  grid-template-columns: v-bind("showArticlesSidebar ? '280px 1fr 350px' : '1fr 350px'");
  gap: 0;
  overflow: hidden;
}

.article-viewer {
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  background: white;
  overflow: hidden;
}

.article-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 3rem;
}

.article-content {
  line-height: 1.6;
  color: #333;
}

.wikipedia-article {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Verdana, sans-serif;
  line-height: 1.6;
  color: #202122;
}

.wikipedia-article p {
  margin-bottom: 0.8rem;
}

.wikipedia-article h1,
.wikipedia-article h2,
.wikipedia-article h3,
.wikipedia-article h4,
.wikipedia-article h5,
.wikipedia-article h6 {
  font-weight: 600;
  margin-top: 1.2rem;
  margin-bottom: 0.6rem;
  line-height: 1.3;
}

.wikipedia-article h1 {
  font-size: 1.8rem;
  border-bottom: 1px solid #a2a9b1;
  padding-bottom: 0.3rem;
}

.wikipedia-article h2 {
  font-size: 1.5rem;
  border-bottom: 1px solid #d3d3d3;
  padding-bottom: 0.3rem;
}

.wikipedia-article h3 {
  font-size: 1.2rem;
}

.wikipedia-article a {
  color: #0645ad;
  text-decoration: none;
}

.wikipedia-article a:visited {
  color: #0b0764;
}

.wikipedia-article a:hover {
  text-decoration: underline;
}

.wikipedia-article img {
  max-width: 100%;
  height: auto;
  margin: 0.5rem 0;
}

.wikipedia-article table {
  border-collapse: collapse;
  margin: 1rem 0;
  width: 100%;
  background: white;
}

.wikipedia-article table th,
.wikipedia-article table td {
  border: 1px solid #a2a9b1;
  padding: 0.5rem;
}

.wikipedia-article table th {
  background-color: #eaeaff;
  font-weight: 600;
  text-align: left;
}

.wikipedia-article ul,
.wikipedia-article ol {
  margin: 1rem 0;
  padding-left: 2rem;
}

.wikipedia-article li {
  margin-bottom: 0.5rem;
}

.article-content {
  line-height: 1.6;
  color: #333;
}

.article-content h1,
.article-content h2,
.article-content h3 {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.article-content h1 {
  font-size: 2rem;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

.article-content h2 {
  font-size: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

.article-content h3 {
  font-size: 1.25rem;
}

.article-content p {
  margin-bottom: 1rem;
}

.article-content a {
  color: #0645ad;
  text-decoration: none;
}

.article-content a:hover {
  text-decoration: underline;
}

.article-content img {
  max-width: 100%;
  height: auto;
  margin: 1rem 0;
}

.article-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.article-content table th,
.article-content table td {
  border: 1px solid #e0e0e0;
  padding: 0.5rem;
  text-align: left;
}

.article-content table th {
  background-color: #f0f0f0;
  font-weight: 600;
}

.loading,
.error {
  padding: 2rem;
  text-align: center;
  color: #666;
  font-size: 1.1rem;
}

.error {
  color: #d32f2f;
}


.articles-sidebar {
  background: #f9f9f9;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  background: white;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 0.95rem;
  color: #1a1a1a;
  font-weight: 700;
}

.close-sidebar {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
  transition: color 0.2s;
}

.close-sidebar:hover {
  color: #1a1a1a;
}

.articles-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.article-item {
  background: none;
  border: none;
  border-bottom: 1px solid #e0e0e0;
  padding: 0.75rem 1rem;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: background 0.2s;
  color: #333;
  font-size: 0.85rem;
}

.article-item:hover {
  background: #f0f0f0;
}

.article-item.active {
  background: #e8ecff;
  color: #667eea;
  font-weight: 600;
  border-left: 3px solid #667eea;
  padding-left: calc(1rem - 3px);
}

.article-num {
  color: #999;
  font-weight: 600;
  min-width: 25px;
}

.article-item.active .article-num {
  color: #667eea;
}

.article-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.article-content-scroll {
  flex: 1;
  overflow-y: auto;
  position: relative;
  padding: 2rem;
  background: white;
}

.wikipedia-article h1 {
  font-size: 2rem;
  color: #1a1a1a;
  margin-top: 0;
  margin-bottom: 1rem;
  padding-bottom: 0;
  border-bottom: none;
  font-weight: 700;
}

.article-header {
  padding: 1rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.article-meta {
  display: flex;
  gap: 1rem;
  margin-top: 0.75rem;
}

.lang-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
  text-decoration: none;
}

.lang-btn:hover {
  text-decoration: underline;
}

.article-tabs {
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 1.5rem;
}

.tab {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 0.95rem;
  padding: 0;
  padding-bottom: 0.5rem;
  font-weight: 500;
}

.tab:hover {
  color: #5568d3;
}

.tab.active {
  color: #1a1a1a;
  border-bottom: 2px solid #667eea;
  padding-bottom: calc(0.5rem - 2px);
}

.tab.tools {
  margin-left: auto;
}

.article-body {
  line-height: 1.8;
  color: #333;
  font-size: 1rem;
}

.article-body p {
  margin-bottom: 1rem;
}

.article-body h2 {
  font-size: 1.6rem;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  color: #1a1a1a;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.75rem;
  font-weight: 700;
}

.article-body h3 {
  font-size: 1.2rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #333;
  font-weight: 700;
}

.article-body a {
  color: #667eea;
  text-decoration: none;
}

.article-body a:hover {
  text-decoration: underline;
}

.review-sidebar {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  overflow-y: auto;
  background: #f9f9f9;
  gap: 1rem;
}

.article-metadata {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.metadata-item {
  display: grid;
  grid-template-columns: 20px 1fr;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.85rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.metadata-item:last-child {
  border-bottom: none;
}

.metadata-icon {
  font-size: 1rem;
  text-align: center;
}

.metadata-label {
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.3px;
}

.metadata-value {
  color: #1a1a1a;
  font-weight: 700;
  text-align: right;
}

.review-decision-box {
  padding: 1rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.box-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.decision-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.decision-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.8rem;
  border: 2px solid #d0d0d0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.decision-btn.accept {
  border-color: #2e7d32;
  color: #2e7d32;
}

.decision-btn.accept:hover {
  background: #f1f8f6;
}

.decision-btn.accept.active {
  background: #2e7d32;
  color: white;
}

.decision-btn.reject {
  border-color: #d32f2f;
  color: #d32f2f;
}

.decision-btn.reject:hover {
  background: #fef5f5;
}

.decision-btn.reject.active {
  background: #d32f2f;
  color: white;
}

.btn-icon {
  font-weight: 700;
  font-size: 1rem;
}

.jury-review-box,
.comment-box {
  padding: 1rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.comment-textarea {
  width: 100%;
  min-height: 180px;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.85rem;
  resize: vertical;
  transition: border-color 0.2s;
}

.comment-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.btn-view-jury-reviews {
  width: 100%;
  padding: 0.9rem;
  background: white;
  border: 2px solid #667eea;
  color: #667eea;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
  text-transform: capitalize;
}

.btn-view-jury-reviews:hover {
  background: #f0f4ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 0.75rem;
  flex-direction: column;
}

.sidebar-footer .btn {
  width: 100%;
  padding: 0.6rem;
  font-size: 0.85rem;
}

.btn {
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary {
  background-color: #f8f9fa;
  border: 1px solid #c8c8c8;
  color: #333;
}

.btn-secondary:hover {
  background-color: #e9ecef;
}

.btn-submit {
  background-color: #28a745;
  color: white;
}

.btn-submit:hover {
  background-color: #218838;
}

/* Language indicators for multilingual article display */
.wikipedia-article :deep(.language-notice) {
  background: #fff3cd;
  color: #856404;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border: 1px solid #ffc107;
}

.wikipedia-article :deep(a) {
  color: #2196f3;
  text-decoration: none;
}

.wikipedia-article :deep(a:hover) {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .review-content {
    grid-template-columns: 1fr;
  }

  .article-viewer {
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }

  .review-sidebar {
    max-height: 300px;
  }

  .review-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .review-header h1 {
    width: 100%;
  }
}
</style>
