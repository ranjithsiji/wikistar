<script setup>
import { onMounted, ref } from 'vue'
import NavBar from './components/NavBar.vue'
import AppFooter from './components/AppFooter.vue'
import { useAuthStore } from './store'

const auth = useAuthStore()

// The OAuth callback bounces home with ?login=cancelled|failed when the
// user rejects the request on meta or the token exchange breaks.
const loginNotice = ref('')
const NOTICES = {
  cancelled: 'Login was cancelled on Wikimedia — nothing was saved. You can try again anytime.',
  failed: 'Login failed — please try again. If it keeps happening, report an issue.'
}

onMounted(() => {
  auth.fetchUser()
  const params = new URLSearchParams(window.location.search)
  const reason = params.get('login')
  if (reason) {
    loginNotice.value = NOTICES[reason] || NOTICES.failed
    params.delete('login')
    const query = params.toString()
    window.history.replaceState({}, '',
      window.location.pathname + (query ? `?${query}` : ''))
  }
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <NavBar />
    <div v-if="loginNotice"
         class="bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300
                border-b border-amber-200 dark:border-amber-900">
      <div class="max-w-6xl mx-auto px-4 py-2.5 flex items-center gap-3 text-sm">
        <span class="flex-1">{{ loginNotice }}</span>
        <button class="font-semibold hover:underline" @click="loginNotice = ''">
          Dismiss
        </button>
      </div>
    </div>
    <main class="max-w-6xl w-full mx-auto px-4 py-6 flex-1">
      <router-view />
    </main>
    <AppFooter />
  </div>
</template>
