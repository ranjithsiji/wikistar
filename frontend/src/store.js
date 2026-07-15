import { defineStore } from 'pinia'
import api from './api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null, loaded: false }),
  getters: {
    isLoggedIn: (s) => !!s.user,
    isAdmin: (s) => !!s.user?.is_admin
  },
  actions: {
    async fetchUser () {
      try {
        const { data } = await api.me()
        this.user = data.user
      } finally {
        this.loaded = true
      }
    }
  }
})
