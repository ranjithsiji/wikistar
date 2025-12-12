<template>
  <div class="jury-articles-fullscreen">
    <!-- Header -->
    <div class="jury-articles-header">
      <button class="back-btn" @click="goBack">← Back</button>
      <h1>Jury Review</h1>
      <div class="header-actions">
        <span class="article-count">{{ articles.length }} Articles</span>
      </div>
    </div>

    <!-- Jury Members Filter Bar -->
    <div class="jury-filter-bar">
      <div style="display: flex; justify-content: flex-end; gap: 10px; padding-right: 10px;">
        <small v-for="jury in juries" :key="jury.id">{{ jury.username }}</small>
      </div>
    </div>

    <!-- Main Content -->
    <div class="jury-articles-content">
      <div class="jury-list-container">
        <div
          v-for="article in articles"
          :key="article.id"
          class="jury-article-item"
        >
          <a 
            :href="getWikipediaUrl(article.title)" 
            target="_blank" 
            class="jury-article-link"
          >
            {{ article.title }}
          </a>
          
          <button 
            class="btn-judge-icon" 
            @click="openArticleReview(article)"
            title="Review this article"
          >📝</button>
          
          <div class="jury-review-status">
            <div
              v-for="jury in juries"
              :key="jury.id"
              class="review-box"
              :class="{ reviewed: isArticleReviewedBy(article, jury) }"
              @click="toggleReview(article, jury)"
              @click.stop
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer with Save Button -->
    <div class="jury-articles-footer">
      <button class="btn btn-secondary" @click="goBack">Close</button>
      <button class="btn btn-submit" @click="saveJuryReviews">Save</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const articles = ref([])
const juries = ref([])
const reviewStatus = ref({}) // Track review status
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
      
      // Load juries from editathon
      juries.value = data.juries || []
      
      // Load articles from editathon leaderboard
      const articlesSet = new Set()
      const articlesMap = {}
      
      if (data.leaderboard) {
        data.leaderboard.forEach((user, userIndex) => {
          if (user.articles) {
            user.articles.forEach((article, articleIndex) => {
              const key = article.title
              if (!articlesMap[key]) {
                articlesMap[key] = {
                  id: articlesSet.size + 1,
                  title: article.title,
                  author: article.author
                }
                articlesSet.add(key)
              }
            })
          }
        })
      }
      
      articles.value = Object.values(articlesMap)
      
      // Initialize review status
      articles.value.forEach(article => {
        reviewStatus.value[article.id] = {}
        juries.value.forEach(jury => {
          reviewStatus.value[article.id][jury.id] = false
        })
      })
    })
    .catch(error => {
      console.error('Error loading editathon data:', error)
      // Fallback to empty data
      juries.value = []
      articles.value = []
    })
}

function getWikipediaUrl(title) {
  return `https://${wikiLanguage.value}.wikipedia.org/wiki/${encodeURIComponent(title)}`
}

function isArticleReviewedBy(article, jury) {
  return reviewStatus.value[article.id]?.[jury.id] || false
}

function toggleReview(article, jury) {
  if (!reviewStatus.value[article.id]) {
    reviewStatus.value[article.id] = {}
  }
  reviewStatus.value[article.id][jury.id] = !reviewStatus.value[article.id][jury.id]
}

function openArticleReview(article) {
  // Open review for this article
  router.push({
    name: 'ArticleReviewFullScreen',
    params: { id: route.params.id },
    query: { articleId: article.id, title: article.title }
  })
}

function closeReviewModal() {
  // This is no longer used
}

function getWikipediaIframeUrl(title) {
  const language = 'en'
  return `https://${language}.wikipedia.org/wiki/${encodeURIComponent(title)}`
}

function saveJuryReviews() {
  console.log('Saving jury reviews...', reviewStatus.value)
  // Call API to save reviews
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.jury-articles-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.jury-articles-header {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 1.5rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
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

.jury-articles-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #1a1a1a;
  flex: 1;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.article-count {
  background: #f0f4ff;
  color: #667eea;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
}

.jury-filter-bar {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 0.75rem 2rem;
}

.jury-articles-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
}

.jury-list-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.jury-article-item {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  transition: all 0.2s;
}

.jury-article-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #d0d0d0;
}

.jury-article-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
  flex: 1;
}

.jury-article-link:hover {
  color: #5568d3;
  text-decoration: underline;
}

.btn-judge-icon {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.btn-judge-icon:hover {
  transform: scale(1.2);
}

.jury-review-status {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.review-box {
  width: 32px;
  height: 32px;
  border: 2px solid #d0d0d0;
  border-radius: 4px;
  cursor: pointer;
  background: white;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.review-box:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.review-box.reviewed {
  background: #2e7d32;
  border-color: #2e7d32;
  color: white;
  font-weight: 700;
}

.review-box.reviewed::after {
  content: '✓';
}

.jury-articles-footer {
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 1rem 2rem;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
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

@media (max-width: 768px) {
  .jury-articles-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .jury-articles-header h1 {
    width: 100%;
  }

  .jury-article-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
