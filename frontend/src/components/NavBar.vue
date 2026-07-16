<script setup>
import api from '../api'
import { useAuthStore } from '../store'
import { useTheme } from '../theme'

const auth = useAuthStore()
const { theme, cycleTheme } = useTheme()

const themeTitles = {
  light: 'Theme: light — click for dark',
  dark: 'Theme: dark — click to follow system',
  system: 'Theme: system — click for light',
}
</script>

<template>
  <nav class="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">
      <router-link to="/" class="font-bold text-lg tracking-tight">
        Wiki<span class="text-blue-600 dark:text-blue-400">STAR</span>
      </router-link>
      <div class="flex-1"></div>
      <button class="btn !px-2" :title="themeTitles[theme]"
              :aria-label="themeTitles[theme]" @click="cycleTheme">
        <!-- sun -->
        <svg v-if="theme === 'light'" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
        <!-- moon -->
        <svg v-else-if="theme === 'dark'" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
        </svg>
        <!-- monitor (system) -->
        <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <path d="M8 21h8m-4-4v4" />
        </svg>
      </button>
      <router-link v-if="auth.isLoggedIn" to="/campaigns/new" class="btn">
        + New campaign
      </router-link>
      <router-link v-if="auth.isAdmin" to="/admin" class="btn">Admin</router-link>
      <template v-if="auth.isLoggedIn">
        <span class="text-sm text-neutral-500 dark:text-neutral-400">{{ auth.user.username }}</span>
        <a class="btn" :href="api.logoutUrl">Logout</a>
      </template>
      <a v-else class="btn-primary" :href="api.loginUrl">Login with Wikimedia</a>
    </div>
  </nav>
</template>
