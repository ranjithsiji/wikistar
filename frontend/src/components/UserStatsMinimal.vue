<template>
  <div class="user-stats-compact">
    <div class="compact-header">
      <h4>User Statistics</h4>
    </div>

    <div class="compact-search">
      <input
        type="text"
        v-model="username"
        placeholder="Enter username..."
        @input="handleInput"
        @keyup.enter="fetchStats"
        autocomplete="off"
      >
      <button @click="fetchStats" :disabled="loading" class="btn-search">
        <span v-if="!loading">Search</span>
        <span v-else>Loading...</span>
      </button>

      <!-- Username Suggestions -->
      <div v-if="suggestions.length > 0" class="suggestions-compact">
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

    <!-- Error -->
    <div v-if="error" class="error-tiny">{{ error }}</div>

    <!-- Stats Display -->
    <div v-if="userData" class="stats-result">
      <div class="result-header">
        <span class="result-avatar">{{ userData.name.charAt(0).toUpperCase() }}</span>
        <div class="result-info">
          <span class="result-name">{{ userData.name }}</span>
          <span v-if="userData.blockinfo" class="badge-blocked">Blocked</span>
          <span v-else class="badge-active">Active</span>
        </div>
      </div>

      <div class="result-stats">
        <div class="r-stat">
          <span class="r-label">Edit Count</span>
          <span class="r-value">{{ userData.editcount?.toLocaleString() || 0 }}</span>
        </div>
        <div class="r-stat">
          <span class="r-label">User ID</span>
          <span class="r-value">{{ userData.userid || 'N/A' }}</span>
        </div>
        <div class="r-stat">
          <span class="r-label">Registered</span>
          <span class="r-value">{{ formatDate(userData.registration) }}</span>
        </div>
      </div>

      <a :href="`https://en.wikipedia.org/wiki/User:${username}`" target="_blank" class="view-link">View Profile →</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const username = ref('')
const userData = ref(null)
const error = ref(null)
const loading = ref(false)
const suggestions = ref([])
let debounceTimer = null

async function handleInput() {
  const query = username.value.trim()
  
  clearTimeout(debounceTimer)
  error.value = null
  userData.value = null

  if (query.length < 2) {
    suggestions.value = []
    return
  }

  debounceTimer = setTimeout(async () => {
    try {
      const url = `https://en.wikipedia.org/w/api.php?action=query&list=allusers&auprefix=${encodeURIComponent(query)}&aulimit=5&format=json&origin=*`
      const response = await fetch(url)
      const data = await response.json()
      suggestions.value = data.query?.allusers || []
    } catch (err) {
      console.error('Error fetching suggestions:', err)
    }
  }, 300)
}

function selectSuggestion(selectedUsername) {
  username.value = selectedUsername
  suggestions.value = []
  fetchStats()
}

async function fetchStats() {
  const query = username.value.trim()
  
  if (!query) {
    error.value = 'Please enter a username'
    return
  }

  loading.value = true
  error.value = null
  userData.value = null

  try {
    const url = `https://en.wikipedia.org/w/api.php?action=query&list=users&ususers=${encodeURIComponent(query)}&usprop=blockinfo|groups|editcount|registration|gender&format=json&origin=*`
    
    const response = await fetch(url)
    const data = await response.json()
    
    loading.value = false

    if (data.query && data.query.users && data.query.users[0]) {
      const userInfo = data.query.users[0]
      if (userInfo.missing !== undefined) {
        error.value = `User "${query}" not found`
      } else if (userInfo.invalid !== undefined) {
        error.value = 'Invalid username format'
      } else {
        userData.value = userInfo
      }
    } else {
      error.value = 'User not found'
    }
  } catch (err) {
    loading.value = false
    error.value = 'Connection error'
    console.error(err)
  }
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.user-stats-compact {
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  padding: 1.25rem;
  margin-top: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.compact-header {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #f0f0f0;
}

.compact-header h4 {
  margin: 0;
  font-size: 1.05rem;
  color: #1a1a1a;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.compact-search {
  position: relative;
  display: flex;
  gap: 0.6rem;
  margin-bottom: 1rem;
}

.compact-search input {
  flex: 1;
  padding: 0.7rem 0.9rem;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: all 0.2s;
  background: #fafafa;
  color: #333;
}

.compact-search input::placeholder {
  color: #999;
}

.compact-search input:focus {
  outline: none;
  border-color: #667eea;
  background: #ffffff;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.08);
}

.btn-search {
  padding: 0.7rem 1.2rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
  letter-spacing: 0.3px;
}

.btn-search:hover:not(:disabled) {
  background: #5568d3;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.25);
}

.btn-search:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* Suggestions */
.suggestions-compact {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d0d0d0;
  border-top: none;
  border-radius: 0 0 6px 6px;
  max-height: 220px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  margin-top: -1px;
}

.suggestion-item {
  padding: 0.7rem 0.9rem;
  cursor: pointer;
  transition: all 0.15s;
  border-bottom: 1px solid #f5f5f5;
  font-size: 0.9rem;
  color: #333;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: #f7f9ff;
  color: #667eea;
  font-weight: 500;
  padding-left: 1.1rem;
}

.error-tiny {
  background: #fef2f2;
  color: #d32f2f;
  padding: 0.75rem 0.9rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  border-left: 3px solid #d32f2f;
  font-weight: 500;
}

/* Stats Result */
.stats-result {
  border-top: 1px solid #f0f0f0;
  padding-top: 1rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.result-avatar {
  width: 40px;
  height: 40px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.95rem;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.2);
}

.result-info {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.result-name {
  font-weight: 700;
  color: #1a1a1a;
  font-size: 0.95rem;
}

.badge-active {
  color: #2e7d32;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-blocked {
  color: #d32f2f;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.result-stats {
  margin-bottom: 1rem;
  background: #f7f9fc;
  padding: 0.9rem;
  border-radius: 6px;
  border: 1px solid #e8ecf1;
}

.r-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: #555;
  margin-bottom: 0.5rem;
}

.r-stat:last-child {
  margin-bottom: 0;
}

.r-label {
  font-weight: 600;
  color: #666;
  letter-spacing: 0.2px;
}

.r-value {
  color: #1a1a1a;
  font-weight: 700;
  font-size: 0.9rem;
}

.view-link {
  display: inline-block;
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.85rem;
  transition: all 0.3s;
  letter-spacing: 0.3px;
}

.view-link:hover {
  color: #5568d3;
  text-decoration: underline;
}
</style>
