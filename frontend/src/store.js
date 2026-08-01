import { defineStore } from 'pinia'
import api from './api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null, loaded: false }),
  getters: {
    isLoggedIn: (s) => !!s.user,
    isAdmin: (s) => !!s.user?.is_admin,
    // A logged-in user who has set neither preferred languages nor home
    // wikis: preferences shape the suggested-article links and language
    // pickers, so the app prompts once rather than quietly defaulting.
    needsPreferences: (s) => !!s.user && !s.user.has_preferences
  },
  actions: {
    async fetchUser () {
      try {
        const { data } = await api.me()
        this.user = data.user
      } finally {
        this.loaded = true
      }
    },
    // Called after saving preferences so the prompt reacts immediately
    // instead of waiting for the next /api/me.
    setHasPreferences (value) {
      if (this.user) this.user.has_preferences = value
    }
  }
})
