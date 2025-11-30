// src/services/api.js

const API_BASE = 'http://localhost:5000/api'

// Fetch all editathons - REAL DATA from MariaDB
export async function fetchEditathons() {
  try {
    const response = await fetch(`${API_BASE}/editathons`)
    if (!response.ok) throw new Error('Failed to fetch editathons')
    return await response.json()
  } catch (error) {
    console.error('Error fetching editathons:', error)
    throw error // No fallback - force real data
  }
}

// Fetch personal cabinet data - REAL DATA from MariaDB
export async function fetchPersonalCabinet(username) {
  try {
    const response = await fetch(`${API_BASE}/personal-cabinet/${username}`)
    if (!response.ok) throw new Error('Failed to fetch personal cabinet data')
    return await response.json()
  } catch (error) {
    console.error('Error fetching personal cabinet:', error)
    throw error // No fallback - force real data
  }
}

// Fetch editathon dashboard data - REAL DATA from MariaDB
export async function fetchEditathonDashboard(editathonId) {
  try {
    const response = await fetch(`${API_BASE}/editathon/${editathonId}`)
    if (!response.ok) throw new Error('Failed to fetch editathon data')
    return await response.json()
  } catch (error) {
    console.error('Error fetching editathon dashboard:', error)
    throw error // No fallback - force real data
  }
}

// Submit article to editathon
export async function submitArticle(editathonId, articleData) {
  try {
    const response = await fetch(`${API_BASE}/editathon/${editathonId}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(articleData)
    })
    if (!response.ok) throw new Error('Failed to submit article')
    return await response.json()
  } catch (error) {
    console.error('Error submitting article:', error)
    throw error
  }
}

// Judge article
export async function judgeArticle(editathonId, judgeData) {
  try {
    const response = await fetch(`${API_BASE}/editathon/${editathonId}/judge`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(judgeData)
    })
    if (!response.ok) throw new Error('Failed to judge article')
    return await response.json()
  } catch (error) {
    console.error('Error judging article:', error)
    throw error
  }
}

// Get user statistics - REAL DATA from MariaDB
export async function fetchUserStats(username) {
  try {
    const response = await fetch(`${API_BASE}/user/${username}`)
    if (!response.ok) throw new Error('Failed to fetch user stats')
    return await response.json()
  } catch (error) {
    console.error('Error fetching user stats:', error)
    throw error // No fallback - force real data
  }
}

// Create new editathon - Save to backend
export async function createEditathon(editathonData) {
  try {
    const response = await fetch(`${API_BASE}/editathons/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editathonData)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to create editathon')
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error creating editathon:', error)
    throw error
  }
}

// Fetch editathon data for judge view - alias for fetchEditathonDashboard
export async function fetchEditathon(editathonId) {
  return fetchEditathonDashboard(editathonId)
}

// Toggle review status for article - PLACEHOLDER (backend doesn't support yet)
export async function toggleReview(articleId, username) {
  // TODO: Implement when backend supports review toggling
  console.log(`Toggling review for article ${articleId} by ${username}`)
  // For now, just return success
  return { success: true }
}

// Fetch user's pending editathons
export async function fetchUserPendingEditathons(username) {
  try {
    const response = await fetch(`${API_BASE}/user/${username}/pending-editathons`)
    if (!response.ok) throw new Error('Failed to fetch pending editathons')
    return await response.json()
  } catch (error) {
    console.error('Error fetching pending editathons:', error)
    return [] // Return empty array if endpoint doesn't exist yet
  }
}
