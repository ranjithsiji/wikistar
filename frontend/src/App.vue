<script setup>
import { onMounted, ref } from 'vue'
import { CdxMessage } from '@wikimedia/codex'
import NavBar from './components/NavBar.vue'
import AppFooter from './components/AppFooter.vue'
import { useAuthStore } from './store'

const auth = useAuthStore()

// The OAuth callback bounces home with ?login=cancelled|failed when the
// user rejects the request on meta or the token exchange breaks.
const loginNotice = ref('')
const loginNoticeType = ref('warning')
const NOTICES = {
  cancelled: ['warning', 'Login was cancelled on Wikimedia — nothing was saved. You can try again anytime.'],
  failed: ['error', 'Login failed — please try again. If it keeps happening, report an issue.']
}

onMounted(() => {
  auth.fetchUser()
  const params = new URLSearchParams(window.location.search)
  const reason = params.get('login')
  if (reason) {
    const [type, text] = NOTICES[reason] || NOTICES.failed
    loginNoticeType.value = type
    loginNotice.value = text
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
    <div v-if="loginNotice" class="max-w-6xl w-full mx-auto px-4 pt-4">
      <cdx-message :type="loginNoticeType" :allow-user-dismiss="true"
                   @user-dismissed="loginNotice = ''">
        {{ loginNotice }}
      </cdx-message>
    </div>
    <main class="max-w-6xl w-full mx-auto px-4 py-6 flex-1">
      <router-view />
    </main>
    <AppFooter />
  </div>
</template>
