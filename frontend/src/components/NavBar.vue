<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../store'
import { useTheme } from '../theme'

const auth = useAuthStore()
const router = useRouter()
const { theme, cycleTheme } = useTheme()

const themeTitles = {
  light: 'Theme: light — click for dark',
  dark: 'Theme: dark — click to follow system',
  system: 'Theme: system — click for light',
}

const navLinks = computed(() => [
  { to: '/contests', label: 'Contests' },
  { to: '/about', label: 'About' },
  ...(auth.isAdmin ? [{ to: '/admin', label: 'Admin' }] : []),
])

const menuOpen = ref(false)
const menuRoot = ref(null)

function onDocumentClick (e) {
  if (menuRoot.value && !menuRoot.value.contains(e.target)) menuOpen.value = false
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
router.afterEach(() => { menuOpen.value = false })
</script>

<template>
  <nav class="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">
      <router-link to="/" class="font-bold text-lg tracking-tight flex items-center gap-1.5">
        <span aria-hidden="true">🌟</span>
        Wiki<span class="text-blue-600 dark:text-blue-400">STAR</span>
      </router-link>
      <div class="flex items-center gap-1 ml-2">
        <router-link v-for="link in navLinks" :key="link.to" :to="link.to"
                     class="rounded-lg px-3 py-1.5 text-sm font-medium text-neutral-600 dark:text-neutral-300
                            hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100"
                     active-class="!text-blue-700 dark:!text-blue-400 bg-blue-50 dark:bg-blue-950/50">
          {{ link.label }}
        </router-link>
      </div>
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

      <div v-if="auth.isLoggedIn" ref="menuRoot" class="relative">
        <button class="btn" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen">
          {{ auth.user.username }}
          <svg class="w-3.5 h-3.5 transition-transform" :class="menuOpen && 'rotate-180'"
               viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>
        <div v-if="menuOpen"
             class="absolute right-0 mt-1.5 w-44 card shadow-lg py-1 z-20">
          <router-link to="/dashboard"
                       class="block px-3 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800">
            Dashboard
          </router-link>
          <router-link to="/preferences"
                       class="block px-3 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800">
            Preferences
          </router-link>
          <router-link v-if="auth.isAdmin" to="/admin"
                       class="block px-3 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800">
            Administration
          </router-link>
          <div class="my-1 border-t border-neutral-200 dark:border-neutral-800"></div>
          <a :href="api.logoutUrl"
             class="block px-3 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800">
            Logout
          </a>
        </div>
      </div>
      <a v-else class="btn-primary" :href="api.loginUrl">Login with Wikimedia</a>
    </div>
  </nav>
</template>
