<template>
  <div class="editathon-dashboard">
    <!-- Utility Header -->
    <div class="utility-header">
    </div>

    <div class="title-and-buttons">
      <h1 class="main-title">Wikipedia: Women's Edit-a-thon 2025</h1>
      <div class="action-buttons">
        <button class="btn btn-submit" @click="openSubmitModal">Submit Article</button>
        <button class="btn btn-judge" @click="showJudgeModal = true">Judge</button>
      </div>
    </div>

    <!-- Status Bar -->
    <div class="status-bar">
      <div><p>The editathon has finished</p></div>
    </div>

    <!-- Top Section: Overview and Inspector -->
    <div class="top-section-layout">
      <!-- Left: Editathon Overview -->
      <div class="overview-panel">
        <div class="stats-header">
          <h2>📊 Editathon Overview</h2>
        </div>

        <!-- Key Metrics -->
        <div class="key-metrics">
          <div class="metric-card primary">
            <div class="metric-icon">👥</div>
            <div class="metric-content">
              <div class="metric-value">{{ stats.users }}</div>
              <div class="metric-label">Total Participants</div>
            </div>
          </div>

          <div class="metric-card success">
            <div class="metric-icon">📝</div>
            <div class="metric-content">
              <div class="metric-value">{{ stats.articles }}</div>
              <div class="metric-label">Total Articles</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Wiki User Inspector -->
      <div class="inspector-panel">
        <WikiUserInspector />
      </div>
    </div>

    <!-- Jury Members -->
    <div class="jury-members">
      Jury members: 
      <span v-for="(jury, index) in juries" :key="jury.id">
        <a :href="getUserWikipediaUrl(jury.username)" target="_blank" class="wiki-user-link">{{ jury.username }}</a>{{ index < juries.length - 1 ? ', ' : '' }}
      </span>
    </div>

    <!-- Leaderboard Table -->
    <table class="leaderboard">
      <thead>
        <tr><th>User</th><th>Articles</th><th>Points*</th></tr>
      </thead>
      <tbody>
        <template v-for="user in leaderboard" :key="user.id">
          <tr
            class="user-row"
            :class="{ expanded: expandedUser === user.id }"
            @click="toggleUserExpansion(user.id)"
          >
            <td class="user-cell">
              <span class="expand-icon">{{ expandedUser === user.id ? '▼' : '▶' }}</span>
              <a :href="getUserWikipediaUrl(user.username)" target="_blank" class="wiki-user-link">{{ user.username }}</a>
            </td>
            <td>{{ user.articlesCount }}</td>
            <td>{{ user.totalPoints }}</td>
          </tr>

          <!-- Expanded Article Details -->
          <tr v-if="expandedUser === user.id" :key="'details-' + user.id">
            <td colspan="3" class="article-details">
              <div v-for="article in user.articles" :key="article.id" class="article-item">
                <span class="article-info">
                  <a
                    :href="getWikipediaUrl(article.title)"
                    target="_blank"
                    class="article-title"
                  >
                    {{ article.title }}
                  </a>
                  <button 
                    class="btn-judge-small" 
                    @click="openArticleJudge(article)"
                    title="Review this article"
                  >📝</button>
                  <span class="article-meta">{{ formatArticleMeta(article) }}</span>
                </span>
                <span>{{ formatDate(article.addedOn) }}</span>
                <span class="article-points">{{ article.points || 0 }}</span>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <!-- Submit Article Modal Step 1 -->
    <div v-if="showSubmitModal" class="modal-overlay" @click="closeSubmitModal">
      <div class="modal-content submit-modal" @click.stop>
        <div class="modal-header">
          <h3>Submit Article</h3>
          <button class="close-btn" @click="closeSubmitModal">&times;</button>
        </div>
        <div class="modal-body">
          <label for="articleTitle">Search for article on Wikipedia:</label>
          <div class="search-container">
            <input 
              type="text" 
              id="articleTitle" 
              v-model="articleTitle"
              @input="searchWikipediaArticles"
              placeholder="Start typing to search Wikipedia..."
              autocomplete="off"
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
                <div class="suggestion-title">{{ suggestion.title }}</div>
                <div v-if="suggestion.description" class="suggestion-description">
                  {{ suggestion.description }}
                </div>
              </div>
            </div>
            <div v-if="articleTitle.length > 2 && !searchingArticles && articleSuggestions.length === 0" class="no-results">
              No articles found. Try different keywords.
            </div>
          </div>
          <div v-if="selectedArticle" class="selected-article-info">
            <strong>Selected:</strong> {{ selectedArticle.title }}
            <a :href="getWikipediaUrl(selectedArticle.title)" target="_blank" class="view-link">
              View on Wikipedia →
            </a>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeSubmitModal">Cancel</button>
          <button 
            class="btn btn-submit" 
            @click="goToSubmitStep2"
            :disabled="!selectedArticle"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Submit Article Modal Step 2 -->
    <div v-if="showSubmitStep2" class="modal-overlay" @click="showSubmitStep2 = false">
      <div class="modal-content" @click.stop>
        <div class="metadata-box">
          <h4>{{ articleTitle }}</h4>
          <div class="metadata-title-right">{{ getArticlePreview(articleTitle) }}</div>
          <p>The article was created at <strong>{{ getCurrentDateTime() }}</strong></p>
          <p>3,235 bytes, <strong>84 words</strong></p>
          <p>Created by: <strong>Conversion script</strong></p>
          <p>Is in the <strong>main namespace</strong></p>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="goBackToStep1">Back</button>
          <button class="btn btn-submit" @click="addArticle">Add</button>
        </div>
      </div>
    </div>

    <!-- Jury Article List Modal -->
    <div v-if="showJudgeModal" class="modal-overlay" @click="showJudgeModal = false">
      <div class="modal-content jury-modal" @click.stop>
        <span class="judge-close-btn" @click="showJudgeModal = false">&times;</span>
        <h2 style="margin-top: 0;">All Articles (Jury View)</h2>

        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 10px; padding-right: 10px;">
          <small v-for="jury in juries" :key="jury.id">{{ jury.username }}</small>
        </div>

        <div class="jury-list-container">
          <div
            v-for="article in allArticles"
            :key="article.id"
            class="jury-article-item"
            @click.stop
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
              @click="openArticleJudge(article)"
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
        <div class="modal-footer" style="padding-top: 20px;">
          <button class="btn btn-submit" @click="saveJuryReviews">Save</button>
          <button class="btn btn-secondary" @click="showJudgeModal = false">Close</button>
        </div>
      </div>
    </div>

    <!-- Article Judge Modal -->
    <div v-if="showArticleJudge" class="modal-overlay article-judge-modal" @click="showArticleJudge = false">
      <div class="modal-content judge-modal-modern" @click.stop>
        <button class="modern-close-btn" @click="showArticleJudge = false">✕</button>

        <div class="judge-layout">
          <!-- Main Article View -->
          <div class="article-viewer">
            <div class="article-header">
              <h2 class="article-title-main">{{ currentArticle.title }}</h2>
              <a :href="getWikipediaUrl(currentArticle.title)" target="_blank" class="wiki-link">
                View on Wikipedia →
              </a>
            </div>
            <div class="article-content-scroll">
              <div v-html="articleHTML" class="wiki-article-content"></div>
            </div>
          </div>

          <!-- Sidebar with Metadata and Controls -->
          <div class="review-sidebar">
            <!-- User Info Header (Fixed Top) -->
            <div class="user-info-header">
              <div class="user-avatar">👤</div>
              <div class="user-details">
                <div class="user-name">Clinta</div>
                <div class="user-role">Reviewing Article</div>
              </div>
            </div>

            <!-- Scrollable Middle Section -->
            <div>
              <!-- Article Info Grid -->
              <div class="article-info-grid">
                <div class="info-item">
                  <span class="info-icon">👤</span>
                  <span class="info-label">AUTHOR</span>
                  <a :href="getUserWikipediaUrl(currentArticle.author)" target="_blank" class="info-value wiki-user-link">{{ currentArticle.author }}</a>
                </div>
                <div class="info-item">
                  <span class="info-icon">📝</span>
                  <span class="info-label">WORDS</span>
                  <span class="info-value">{{ currentArticle.words }}</span>
                </div>
                <div class="info-item">
                  <span class="info-icon">💾</span>
                  <span class="info-label">BYTES</span>
                  <span class="info-value">{{ currentArticle.bytes }}</span>
                </div>
                <div class="info-item">
                  <span class="info-icon">📅</span>
                  <span class="info-label">ADDED ON</span>
                  <span class="info-value">{{ formatDate(currentArticle.addedOn) }}</span>
                </div>
              </div>

              <!-- Review Decision Section -->
              <div class="review-decision-box">
                <div class="box-title">✅ Review Decision</div>
                <div class="decision-buttons-horizontal">
                  <button class="decision-btn accept" @click="judgeArticle(true)">
                    <span class="btn-icon">✓</span>
                    Accept
                  </button>
                  <button class="decision-btn reject" @click="judgeArticle(false)">
                    <span class="btn-icon">✕</span>
                    Reject
                  </button>
                </div>
              </div>

              <!-- Comment Box -->
              <div class="comment-box">
                <div class="box-title">💬 Comment</div>
                <textarea 
                  v-model="judgeComment" 
                  class="comment-textarea-full"
                  placeholder="Add your review comments..."
                ></textarea>
              </div>
            </div>

            <!-- Fixed Bottom Section -->
            <div>
              <!-- Stats & Actions Combined -->
              <div class="stats-actions-row">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Wikipedia Article Viewer Modal -->
    <WikipediaArticleViewer
      :showModal="showWikipediaViewer"
      :articleTitle="selectedArticleTitle"
      :wikiLanguage="wikiLanguage"
      @close="showWikipediaViewer = false"
      @use-article="handleUseArticle"
    />

    <!-- Bottom Section: Top Contributors -->
    <div class="charts-section">
      <!-- Top Contributors -->
      <div class="chart-section">
        <h3>🏆 Top Contributors</h3>
        <div class="top-contributors">
          <div v-for="(user, index) in topContributors" :key="user.id" class="contributor-item">
            <div class="contributor-rank">{{ index + 1 }}</div>
            <div class="contributor-info">
              <a :href="getUserWikipediaUrl(user.username)" target="_blank" class="contributor-name wiki-user-link">{{ user.username }}</a>
              <div class="contributor-stats">{{ user.articlesCount }} articles · {{ user.totalPoints }} points</div>
            </div>
            <div class="contributor-badge" v-if="index === 0">👑</div>
            <div class="contributor-badge" v-else-if="index === 1">🥈</div>
            <div class="contributor-badge" v-else-if="index === 2">🥉</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { fetchEditathonDashboard, judgeArticle as judgeArticleAPI } from '../services/api'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, Chart, BarController } from 'chart.js'
import WikiUserInspector from '../components/WikiUserInspector.vue'
import WikipediaArticleViewer from '../components/WikipediaArticleViewer.vue'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, BarController)

const route = useRoute()

// Data
const editathon = ref({})
const editathonId = ref(null)
const wikiLanguage = ref('en') // Default to English, will be loaded from editathon data
const stats = ref({
  users: 6,
  articles: 15,
  marks: 12,
  withoutMarks: 3
})

const juries = ref([
  { id: 1, username: 'Meenakshi nandhini' },
  { id: 2, username: 'Ranjithjsiji' },
  { id: 3, username: 'Vijayanrajapuram' }
])

const leaderboard = ref([
  {
    id: 1,
    username: 'Meenakshi nandhini',
    articlesCount: 15,
    totalPoints: 7,
    articles: [
      {
        id: 1,
        title: 'ഷാർലെറ്റ് സോഫിയ ബേൺ',
        addedOn: '2025-03-29T19:38:00',
        points: 0,
        author: 'Meenakshi nandhini',
        words: 150,
        bytes: 2500,
        preview: 'ഈ ലേഖനത്തിന്റെ നിലവാരം പരിശോധിക്കുന്നത് നന്നായിരിക്കും.',
        reviews: ['Vijayanrajapuram']
      },
      {
        id: 2,
        title: 'കാറ്റീന അനറ്റോലിയ്ന പാവ്‌ലെങ്കോ',
        addedOn: '2025-03-29T13:18:00',
        points: 1,
        author: 'Meenakshi nandhini',
        words: 200,
        bytes: 3200,
        preview: 'പ്രാദേശിക ചരിത്രത്തിലെ പ്രമുഖ വ്യക്തി.',
        reviews: ['Vijayanrajapuram']
      }
    ]
  },
  {
    id: 2,
    username: 'Ranjithjsiji',
    articlesCount: 4,
    totalPoints: 1,
    articles: [
      {
        id: 3,
        title: 'ഓൾ ലത',
        addedOn: '2025-03-25T03:09:00',
        points: 0,
        author: 'Ranjithjsiji',
        words: 180,
        bytes: 2800,
        preview: 'സാമൂഹ്യ പ്രവർത്തകയും എഴുത്തുകാരിയും.',
        reviews: []
      }
    ]
  }
])

const unreviewedArticles = ref([
  {
    id: 4,
    title: 'നാൻസി ആദംസ്',
    author: 'User123',
    words: 150,
    bytes: 2500,
    preview: 'ഈ ലേഖനത്തിന്റെ നിലവാരം പരിശോധിക്കുന്നത് നന്നായിരിക്കും.',
    reviews: ['Meenakshi nandhini']
  },
  {
    id: 5,
    title: 'ലൂസി മൗഡ്',
    author: 'User456',
    words: 200,
    bytes: 3200,
    preview: 'പ്രാദേശിക ചരിത്രത്തിലെ പ്രമുഖ വ്യക്തി.',
    reviews: []
  },
  {
    id: 6,
    title: 'ലിന്റിയ വിൽസൺ',
    author: 'User789',
    words: 180,
    bytes: 2800,
    preview: 'സാമൂഹ്യ പ്രവർത്തകയും എഴുത്തുകാരിയും.',
    reviews: ['Meenakshi nandhini', 'Ranjithjsiji']
  }
])

// Modal states
const showSubmitModal = ref(false)
const showSubmitStep2 = ref(false)
const showJudgeModal = ref(false)
const showArticleJudge = ref(false)
const showWikipediaViewer = ref(false)
const expandedUser = ref(1) // Default expanded user

// Form data
const articleTitle = ref('')
const judgeComment = ref('')
const currentArticle = ref({})
const articleHTML = ref('')
const selectedArticleTitle = ref('')
const articleSuggestions = ref([])
const searchingArticles = ref(false)
const selectedArticle = ref(null)
let searchTimeout = null

const totalAccepted = computed(() => {
  return leaderboard.value.reduce((total, user) => {
    return total + user.articles.filter(article => article.points > 0).length
  }, 0)
})

// Computed for charts
const maxArticles = computed(() => {
  return Math.max(...leaderboard.value.map(user => user.articlesCount))
})

const topContributors = computed(() => {
  return [...leaderboard.value]
    .sort((a, b) => b.articlesCount - a.articlesCount)
    .slice(0, 5)
})

// Computed
const allArticles = computed(() => {
  return leaderboard.value.flatMap(user =>
    user.articles.map(article => ({
      ...article,
      author: user.username
    }))
  )
})

// Methods
function formatDate(dateString) {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatArticleMeta(article) {
  if (!article.reviews || article.reviews.length === 0) return 'No reviews yet'
  return article.reviews.map(review => {
    // Handle both old string format and new object format
    if (typeof review === 'string') {
      return review
    }
    // New object format: { juror, decision, points, comment }
    return `${review.juror} ${review.decision} with ${review.points} point${review.points !== 1 ? 's' : ''}`
  }).join(' | ')
}

function toggleUserExpansion(userId) {
  expandedUser.value = expandedUser.value === userId ? null : userId
}

function getWikipediaUrl(title) {
  // Dynamically use the wiki language from editathon data
  return `https://${wikiLanguage.value}.wikipedia.org/wiki/${encodeURIComponent(title)}`
}

function getUserWikipediaUrl(username) {
  // Generate Wikipedia user page URL with correct language
  // User pages are at: https://en.wikipedia.org/wiki/User:Username
  return `https://${wikiLanguage.value}.wikipedia.org/wiki/User:${encodeURIComponent(username)}`
}

async function searchWikipediaArticles() {
  const query = articleTitle.value.trim()
  
  // Clear previous selection when user types
  selectedArticle.value = null
  
  if (query.length < 2) {
    articleSuggestions.value = []
    return
  }

  // Debounce search
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  searchTimeout = setTimeout(async () => {
    searchingArticles.value = true
    try {
      const wikiDomain = `${wikiLanguage.value}.wikipedia.org`
      // Use Wikipedia's opensearch API for suggestions
      const response = await fetch(
        `https://${wikiDomain}/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=10&namespace=0&format=json&origin=*`
      )
      const data = await response.json()
      
      // Format the results: data[1] = titles, data[2] = descriptions, data[3] = URLs
      articleSuggestions.value = data[1].map((title, index) => ({
        title: title,
        description: data[2][index],
        url: data[3][index]
      }))
    } catch (error) {
      console.error('Error searching Wikipedia:', error)
      articleSuggestions.value = []
    } finally {
      searchingArticles.value = false
    }
  }, 300) // Wait 300ms after user stops typing
}

function selectArticleSuggestion(suggestion) {
  selectedArticle.value = suggestion
  articleTitle.value = suggestion.title
  articleSuggestions.value = []
}

function openSubmitModal() {
  // Clear previous selections
  articleTitle.value = ''
  selectedArticle.value = null
  articleSuggestions.value = []
  showSubmitModal.value = true
}

function closeSubmitModal() {
  showSubmitModal.value = false
  // Clear search state
  articleTitle.value = ''
  selectedArticle.value = null
  articleSuggestions.value = []
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
}

async function openArticleJudge(article) {
  currentArticle.value = article
  showArticleJudge.value = true
  showJudgeModal.value = false

  // Fetch article content from Wikipedia
  try {
    const encodedTitle = encodeURIComponent(article.title)
    const wikiDomain = `${wikiLanguage.value}.wikipedia.org`
    // Try to fetch article summary first (more reliable)
    const summaryResponse = await fetch(`https://${wikiDomain}/api/rest_v1/page/summary/${encodedTitle}`)
    
    if (summaryResponse.ok) {
      const data = await summaryResponse.json()
      articleHTML.value = `
        <h2>${data.title}</h2>
        ${data.extract_html || '<p>' + (data.extract || 'No content available') + '</p>'}
        <p><em>Source: <a href="${data.content_urls?.desktop?.page || ''}" target="_blank">View full article on Wikipedia</a></em></p>
      `
    } else if (summaryResponse.status === 404) {
      articleHTML.value = `
        <h2>${article.title}</h2>
        <p class="warning">This article does not exist on Wikipedia yet, or the title may be incorrect.</p>
        <p>You can <a href="https://${wikiDomain}/wiki/${encodedTitle}" target="_blank">view or create it on Wikipedia</a>.</p>
      `
    } else {
      articleHTML.value = '<p>Article content could not be loaded. Please try again later.</p>'
    }
  } catch (error) {
    console.error('Error fetching article:', error)
    articleHTML.value = `
      <h2>${article.title}</h2>
      <p class="error">Error loading article content. Please check your internet connection.</p>
    `
  }
}

function goToSubmitStep2() {
  if (!selectedArticle.value) {
    alert("Please select an article from the Wikipedia suggestions.")
    return
  }
  
  // Use the selected article's title
  articleTitle.value = selectedArticle.value.title
  showSubmitModal.value = false
  showSubmitStep2.value = true
}

function goBackToStep1() {
  showSubmitStep2.value = false
  showSubmitModal.value = true
  // Keep the selected article when going back
}

async function addArticle() {
  try {
    const response = await fetch(`http://localhost:5000/api/editathon/${route.params.id}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'Clinta',
        article_title: articleTitle.value
      })
    })

    if (response.ok) {
      alert(`Article "${articleTitle.value}" successfully added by Clinta!`)
      showSubmitStep2.value = false
      articleTitle.value = ''
      // Refresh the dashboard data
      location.reload()
    } else {
      const error = await response.json()
      alert(`Error: ${error.error}`)
    }
  } catch (error) {
    alert(`Error submitting article: ${error.message}`)
  }
}

function getArticlePreview(title) {
  return `${title} may refer to:`
}

function getCurrentDateTime() {
  return new Date().toLocaleString()
}

function isArticleReviewedBy(article, jury) {
  return article.reviews?.includes(jury.username) || false
}

async function judgeArticle(accepted) {
  try {
    const points = accepted ? 1 : 0
    const status = accepted ? 'accepted' : 'rejected'
    
    // Build reviewer note with name and decision
    const reviewerName = 'Clinta' // Current reviewer
    const reviewerNote = `${reviewerName} ${status} with ${points} point${points !== 1 ? 's' : ''}`
    
    const judgeData = {
      article_title: currentArticle.value.title,
      points: points,
      comment: reviewerNote,
      reviewer: reviewerName,
      decision: status
    }
    
    // Save review to backend
    const result = await judgeArticleAPI(editathonId.value, judgeData)
    
    if (result.success) {
      // Update current article with review
      currentArticle.value.points = points
      if (!currentArticle.value.reviews) {
        currentArticle.value.reviews = []
      }
      currentArticle.value.reviews.push(reviewerName)
      
      // Show success message
      alert(`✓ Review saved! ${reviewerNote}`)
      
      // Close modal
      showArticleJudge.value = false
      judgeComment.value = ''
    } else {
      alert('Error saving review. Please try again.')
    }
  } catch (error) {
    console.error('Error saving review:', error)
    alert('Failed to save review. Please check your connection.')
  }
}

function skipArticle() {
  showArticleJudge.value = false
  judgeComment.value = ''
}

function saveAndNext() {
  judgeArticle(true) // Auto-accept for demo
}

function toggleReview(article, jury) {
  const index = article.reviews.indexOf(jury.username)
  if (index > -1) {
    article.reviews.splice(index, 1)
  } else {
    article.reviews.push(jury.username)
  }
}

function saveJuryReviews() {
  // Save the jury reviews
  // TODO: Send to backend API
  alert('Jury reviews saved successfully!')
  showJudgeModal.value = false
}

function saveReview() {
  // Save the review and close
  // TODO: Send to backend API
  if (judgeComment.value.trim()) {
    alert('Review saved successfully!')
    showArticleJudge.value = false
    judgeComment.value = ''
  } else {
    alert('Please add a comment for your review.')
  }
}

function handleUseArticle(articleTitle) {
  selectedArticleTitle.value = articleTitle
  showWikipediaViewer.value = false
  // Optionally go to submit step 2
  goToSubmitStep2()
}

// Lifecycle
onMounted(async () => {
  editathonId.value = route.params.id
  try {
    // Load editathon data from backend
    const data = await fetchEditathonDashboard(editathonId.value)
    editathon.value = data.editathon
    
    // Set wiki language from editathon data, default to 'ml' if not specified
    wikiLanguage.value = data.editathon?.wiki_language || 'ml'
    
    stats.value = data.stats
    juries.value = data.juries
    leaderboard.value = data.leaderboard
    unreviewedArticles.value = data.unreviewed_articles
  } catch (error) {
    console.error('Error loading editathon:', error)
    // Keep the default mock data if API fails
  }

  // Initialize Chart.js chart
  if (statsChart.value) {
    new Chart(statsChart.value, {
      type: 'bar',
      data: chartData.value,
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'top',
          }
        }
      }
    })
  }
})
</script>

<style scoped>
/* Copy ALL the CSS from your HTML file exactly */
.editathon-dashboard {
  font-family: 'Arial', sans-serif;
  color: #202122;
  margin: 0;
  padding: 20px 40px;
  background-color: #f8f9fa;
}

.utility-header { 
  text-align: right; 
  font-size: 14px; 
  margin-bottom: 30px; 
}

.pencil-icon { 
  float: left; 
  margin-right: 10px; 
  font-size: 24px; 
}

.main-title {
  font-size: 24px;
  font-weight: normal;
  margin-bottom: 10px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 5px;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.admin-section {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.admin-label {
  font-size: 12px;
  color: #54595d;
  font-weight: bold;
  margin-bottom: 5px;
}

.action-buttons { 
  display: flex; 
  gap: 10px; 
}

.btn {
  padding: 4px 8px;
  border: none;
  border-radius: 3px;
  font-weight: bold;
  font-size: 0.85rem;
  cursor: pointer;
  text-align: center;
}

.btn-submit { 
  background-color: #3366cc; 
  color: white; 
}

.btn-judge { 
  background-color: #007bff; 
  color: white; 
}

.btn-secondary { 
  background-color: #f8f9fa; 
  border: 1px solid #c8c8c8; 
  color: #333; 
}

.btn-yes { 
  background-color: #28a745; 
  color: white; 
}

.btn-no { 
  background-color: #dc3545; 
  color: white; 
}

.stats-summary { 
  display: flex; 
  gap: 30px; 
  margin-bottom: 20px; 
}

.stat-box { 
  text-align: center; 
}

.stat-label { 
  font-size: 14px; 
  color: #54595d; 
}

.stat-value { 
  font-size: 36px; 
  font-weight: bold; 
  line-height: 1.1; 
  margin-top: 5px; 
}

.stat-without-marks .stat-value { 
  color: #dc3545; 
}

.jury-members { 
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
  border-radius: 8px;
  border-left: 4px solid #667eea;
  color: #374151;
}

.jury-members a {
  color: #667eea;
  text-decoration: none;
  font-weight: 700;
  transition: color 0.2s;
}

.jury-members a:hover {
  color: #764ba2;
  text-decoration: underline;
}

.wiki-user-link {
  color: #667eea !important;
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid transparent;
}

.wiki-user-link:hover {
  color: #764ba2 !important;
  text-decoration: underline;
  border-bottom-color: #764ba2;
}

.leaderboard { 
  width: 100%; 
  border-collapse: collapse; 
  font-size: 15px; 
}

.leaderboard th, .leaderboard td { 
  padding: 8px 0; 
  text-align: left; 
  border-bottom: 1px solid #eaeaeb; 
}

.leaderboard th { 
  font-weight: bold; 
  color: #54595d; 
  border-bottom: 2px solid #a2a9b1; 
}

.leaderboard th:last-child, .leaderboard td:last-child { 
  text-align: right; 
}

.leaderboard .user-row { 
  cursor: pointer; 
}

.leaderboard .expand-icon { 
  margin-right: 5px; 
  display: inline-block; 
  transition: transform 0.2s; 
}

.expanded .expand-icon { 
  transform: rotate(90deg); 
}

.article-details { 
  padding-left: 30px; 
  background-color: #f9f9f9; 
}

.article-details .article-item { 
  display: flex; 
  justify-content: space-between; 
  padding: 5px 0; 
  border-bottom: 1px dotted #eaeaeb; 
}

.article-details .article-title {
  cursor: pointer;
  display: inline;
  font-size: 14px;
  color: #0645ad;
  text-decoration: none;
}
.article-details .article-title:hover {
  text-decoration: underline;
}

.article-details .article-meta { 
  font-size: 12px; 
  color: #777; 
  margin-top: 2px; 
}

.article-details .article-points { 
  width: 50px; 
  text-align: right; 
  font-weight: bold; 
}

.btn-judge-small {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 0 5px;
  margin-left: 8px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.btn-judge-small:hover {
  opacity: 1;
}

.btn-judge-icon {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 0 8px;
  margin-left: 10px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.btn-judge-icon:hover {
  opacity: 1;
}

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
  padding: 30px; 
  border-radius: 3px; 
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3); 
  width: 450px; 
}

.submit-modal {
  width: 600px;
  max-width: 90%;
  padding: 0;
}

.submit-modal .modal-header {
  padding: 20px 30px;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submit-modal .modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.submit-modal .modal-body {
  padding: 30px;
}

.submit-modal .modal-footer {
  padding: 20px 30px;
  border-top: 1px solid #e5e5e5;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 30px;
  height: 30px;
}

.close-btn:hover {
  color: #333;
}

.search-container {
  position: relative;
  margin-top: 8px;
}

.search-container input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.search-container input:focus {
  outline: none;
  border-color: #0645ad;
}

.loading-indicator {
  padding: 10px;
  text-align: center;
  color: #666;
  font-size: 14px;
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
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.suggestion-item:hover {
  background-color: #f8f9fa;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-title {
  font-weight: 600;
  color: #0645ad;
  margin-bottom: 4px;
}

.suggestion-description {
  font-size: 13px;
  color: #666;
  line-height: 1.4;
}

.no-results {
  padding: 12px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.selected-article-info {
  margin-top: 15px;
  padding: 12px;
  background-color: #e8f5e9;
  border: 1px solid #4caf50;
  border-radius: 4px;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.view-link {
  color: #0645ad;
  text-decoration: none;
  font-weight: 500;
}

.view-link:hover {
  text-decoration: underline;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.jury-modal {
  width: 700px;
  max-width: 90%;
  padding: 20px;
}

.judge-modal {
  width: 100%;
  height: 100vh;
  padding: 0;
  margin: 0;
  display: flex;
  overflow: hidden;
}

.judge-close-btn { 
  position: absolute; 
  top: 10px; 
  right: 10px; 
  font-size: 20px; 
  font-weight: bold; 
  color: #333; 
  cursor: pointer; 
  z-index: 1001; 
  padding: 5px; 
}

.metadata-box { 
  border: 1px solid #dcdcdc; 
  padding: 15px; 
  margin-bottom: 20px; 
  background-color: #f9f9f9; 
  position: relative; 
}

.modal-footer { 
  text-align: right; 
  margin-top: 15px; 
}

.jury-list-container { 
  max-height: 70vh; 
  overflow-y: auto; 
}

.jury-article-item { 
  display: flex; 
  align-items: center; 
  padding: 8px 0; 
  border-bottom: 1px solid #eee; 
}

.jury-article-item a { 
  flex-grow: 1; 
  font-size: 15px; 
  font-weight: bold; 
  cursor: pointer; 
}

.jury-review-status { 
  display: flex; 
  gap: 10px; 
}

.review-box { 
  width: 18px; 
  height: 18px; 
  border: 1px solid #a2a9b1; 
  border-radius: 3px; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  color: white; 
  font-size: 12px; 
  font-weight: bold; 
}

.reviewed {
  background-color: #28a745;
 
}

.reviewed::before {
  content: '✓';
}

.not-reviewed { 
  background-color: #f8f9fa; 
}

.article-judge-modal { 
  padding: 0; 
  align-items: flex-start;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

/* Modern Judge Modal */
.judge-modal-modern {
  width: 100vw !important;
  max-width: 100vw !important;
  height: 100vh !important;
  max-height: 100vh !important;
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 0;
  overflow: hidden;
  margin: 0 !important;
  position: relative;
}

.modern-close-btn {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  width: 48px;
  height: 48px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  color: #374151;
  font-size: 1.5rem;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10000;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.modern-close-btn:hover {
  background: #ef4444;
  color: white;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.judge-layout {
  display: grid;
  grid-template-columns: 1fr 360px;
  height: 100%;
  overflow: hidden;
}

/* Article Viewer */
.article-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
}

.article-header {
  padding: 2rem;
  background: white;
  border-bottom: 2px solid #e5e7eb;
}

.article-title-main {
  font-size: 1.75rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.75rem 0;
}

.wiki-link {
  color: #667eea;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 600;
  transition: color 0.2s;
}

.wiki-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

.article-content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  background: white;
  height: 100%;
}

.wiki-article-content {
  max-width: 100%;
  line-height: 1.7;
  font-size: 1rem;
  color: #374151;
}

.wiki-article-content h1,
.wiki-article-content h2,
.wiki-article-content h3 {
  color: #111827;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.wiki-article-content p {
  margin-bottom: 1rem;
  text-align: justify;
}

.wiki-article-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 1rem 0;
}

.wiki-article-content a {
  color: #667eea;
  text-decoration: none;
}

.wiki-article-content a:hover {
  text-decoration: underline;
}

.wiki-article-content .warning,
.wiki-article-content .error {
  padding: 1rem;
  border-radius: 6px;
  margin: 1rem 0;
}

.wiki-article-content .warning {
  background: #fef3c7;
  color: #92400e;
  border-left: 4px solid #f59e0b;
}

.wiki-article-content .error {
  background: #fee2e2;
  color: #991b1b;
  border-left: 4px solid #ef4444;
}

/* Review Sidebar - Compact & Responsive */
.review-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  overflow: hidden;
  padding: 0;
  gap: 0;
}

/* User Info Header */
.user-info-header {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 0;
  box-shadow: none;
  flex-shrink: 0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.1rem;
}

.user-role {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

/* Scrollable sidebar content */
.review-sidebar > :nth-child(2) {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

/* Article Info Grid - Compact */
.article-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 0.75rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #f3f4f6 100%);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
  margin-bottom: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.4rem;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.info-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #667eea;
  transform: translateY(-2px);
}

.info-icon {
  font-size: 1.2rem;
}

.info-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.info-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #111827;
  word-break: break-word;
}

/* Review Decision Box */
.review-decision-box {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  flex-shrink: 0;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.box-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #374151;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.decision-buttons-horizontal {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.decision-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.7rem;
  border: 2px solid;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.decision-btn .btn-icon {
  font-size: 1.1rem;
}

.decision-btn.accept {
  background: #ecfdf5;
  border-color: #10b981;
  color: #047857;
}

.decision-btn.accept:hover {
  background: #10b981;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.decision-btn.reject {
  background: #fef2f2;
  border-color: #ef4444;
  color: #dc2626;
}

.decision-btn.reject:hover {
  background: #ef4444;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

/* Comment Box */
.comment-box {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.comment-textarea-full {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
  max-height: 120px;
  transition: all 0.3s;
  background: #f9fafb;
  box-sizing: border-box;
}

.comment-textarea-full:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.comment-textarea-full::placeholder {
  color: #d1d5db;
}

/* Fixed Bottom Section */
.review-sidebar > :nth-child(3) {
  flex-shrink: 0;
  padding: 0;
  background: transparent;
  border-top: none;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Stats & Actions Row */
.stats-actions-row {
  display: none;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.mini-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(102, 126, 234, 0.15);
}

.mini-stat-value {
  font-size: 1.125rem;
  font-weight: 800;
  color: white;
}

.mini-stat-label {
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-transform: uppercase;
}

/* Action Buttons Row */
.action-buttons-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 0.5rem;
}

.btn-action {
  padding: 0.625rem;
  border: none;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-action.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-action.secondary {
  background: #f3f4f6;
  color: #6b7280;
  border: 2px solid #e5e7eb;
}

.btn-action.secondary:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
  transform: translateY(-1px);
}

.sidebar-info {
  font-size: 14px;
  padding-bottom: 20px;
}

.title-and-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  width: 100%;
}

.title-and-buttons .main-title {
  flex: 1;
  margin: 0;
}

.title-and-buttons .action-buttons {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

/* Top Section Layout */
.top-section-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
  margin: 2rem 0;
  padding: 0 1rem;
}

/* Overview Panel */
.overview-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Charts Section (Bottom) */
.charts-section {
  margin: 0 1rem 2rem 1rem;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stats-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 1.5rem 0;
}

/* Key Metrics Cards */
.key-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid;
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-card.primary {
  background: #eff6ff;
  border-left-color: #3b82f6;
}

.metric-card.success {
  background: #f0fdf4;
  border-left-color: #10b981;
}

.metric-card.warning {
  background: #fffbeb;
  border-left-color: #f59e0b;
}

.metric-card.danger {
  background: #fef2f2;
  border-left-color: #ef4444;
}

.metric-icon {
  font-size: 2rem;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}

.metric-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 0.25rem;
}

/* Chart Sections */
.chart-section {
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
}

.chart-section h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 1rem 0;
}

/* Articles per User Bars */
.user-article-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.user-bar-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-bar-label {
  min-width: 150px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-bar-container {
  flex: 1;
  height: 32px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.user-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 0.5rem;
  transition: width 0.5s ease;
  min-width: 40px;
}

.bar-count {
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
}

/* Progress Bar */
.progress-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-bar-large {
  width: 100%;
  height: 40px;
  background: #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1rem;
  transition: width 0.5s ease;
}

.progress-stats {
  text-align: center;
  font-size: 0.875rem;
  color: #6b7280;
}

/* Top Contributors */
.top-contributors {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.contributor-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  transition: transform 0.2s;
}

.contributor-item:hover {
  transform: translateX(4px);
}

.contributor-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 50%;
  font-weight: 700;
  color: #6b7280;
}

.contributor-info {
  flex: 1;
}

.contributor-name {
  font-weight: 600;
  color: #111827;
  font-size: 0.875rem;
}

.contributor-stats {
  font-size: 0.75rem;
  color: #6b7280;
}

.contributor-badge {
  font-size: 1.5rem;
}

/* Inspector Panel */
.inspector-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .top-section-layout {
    grid-template-columns: 1fr;
  }
  
  .key-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .key-metrics {
    grid-template-columns: 1fr;
  }
  
  .user-bar-label {
    min-width: 100px;
    font-size: 0.75rem;
  }
}

/* 1. Main Page Layout (Flexbox for content area) */
.page-wrapper {
  display: flex;
  padding-bottom: 50px; /* Space for the fixed bottom bar */
}

/* 2. Article Content (The main text area) */
.article-content {
  flex-grow: 1;
  padding: 10px 20px 20px 20px;
  max-width: 900px; /* Standard reading width */
  line-height: 1.6;
}

.article-content .warning {
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  color: #856404;
  padding: 12px;
  border-radius: 4px;
  margin: 10px 0;
}

.article-content .error {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin: 10px 0;
}
.article-meta-top {
  text-align: right;
  font-size: 12px;
  color: #555;
  padding-bottom: 5px;
}
.article-title {
  font-size: 2em;
  font-weight: normal;
  margin: 0 0 0.5em 0;
  border-bottom: 1px solid #a2a9b1;
}

/* 3. Wikipedia Warning Box (Needs Image) */
.warning-box {
  border: 1px solid #a2a9b1;
  padding: 10px;
  margin-bottom: 15px;
  background-color: #fcfcfc;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.warning-icon {
  font-size: 24px;
  color: #777;
}
.section-header {
  font-size: 1.5em;
  margin-top: 1em;
  border-bottom: 1px solid #ccc;
  padding-bottom: 3px;
}
.edit-link {
  font-size: 0.7em;
  font-weight: normal;
  margin-left: 10px;
}

/* 4. Infobox/Sidebar Container */
.article-sidebar {
  width: 280px; /* Fixed width for the infobox */
  flex-shrink: 0;
  padding-top: 20px;
  margin-right: 20px;
}
.infobox {
  border: 1px solid #a2a9b1;
  font-size: 13px;
  background-color: #f8f8f8; /* Light gray background */
}
.infobox h4 {
  background-color: #c9c9c9;
  color: #000;
  padding: 5px;
  margin: 0;
  text-align: center;
  font-size: 1.1em;
}
.infobox-row {
  padding: 5px 10px;
  border-bottom: 1px solid #a2a9b1;
  display: flex;
  flex-direction: column;
}
.infobox-label {
  font-weight: bold;
  color: #333;
  margin-bottom: 2px;
}
.infobox-value {
  color: #0645ad; /* Links style */
  font-size: 0.9em;
}

/* 5. Fixed Review Bar (Bottom Overlay) */
.review-control-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: #f0f0f0;
  border-top: 1px solid #ccc;
  padding: 5px 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
  z-index: 100;
}
.review-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}
.comment-input {
  flex-grow: 1;
  margin: 0 15px;
}
.comment-input input {
  width: 100%;
  padding: 8px;
  border: 1px solid #a2a9b1;
  border-radius: 3px;
}
.total-section {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  flex-shrink: 0;
}
.total-value {
  font-weight: bold;
  font-size: 1.5em;
}
</style>