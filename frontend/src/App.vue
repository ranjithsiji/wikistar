<script setup>
import { onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import AppFooter from './components/AppFooter.vue'
import { useAuthStore } from './store'

const auth = useAuthStore()
onMounted(() => auth.fetchUser())
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <NavBar />
    <main class="max-w-6xl w-full mx-auto px-4 py-6 flex-1">
      <router-view />
    </main>
    <AppFooter />
  </div>
</template>
