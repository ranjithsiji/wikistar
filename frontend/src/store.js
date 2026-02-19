import { reactive } from 'vue'
import axios from 'axios'
import router from './router'

export const store = reactive({
  selectedLanguage: null,
  user: null,
  isAuthChecked: false,
  devMode: false
})

// Fetch current user on app load
export async function fetchCurrentUser() {
  try {
    const response = await axios.get('/api/me')
    if (response.data.user) {
      store.user = response.data.user
    }
    store.devMode = response.data.dev_mode || false
  } catch (e) {
    console.error('Failed to fetch user', e)
    store.user = null
  } finally {
    store.isAuthChecked = true
  }
}

// Check if user is authenticated
export function isAuthenticated() {
  return store.user !== null
}

// Logout function
export async function logout() {
  try {
    await axios.get('/api/logout')
  } catch (e) {
    console.error('Logout error:', e)
  } finally {
    // Clear user state regardless of API response
    store.user = null
    store.isAuthChecked = false
    // Redirect to home
    router.push('/')
  }
}
