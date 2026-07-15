<script setup>
import { onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import { useAuthStore } from './store'

const auth = useAuthStore()
onMounted(() => auth.fetchUser())
</script>

<template>
  <NavBar />
  <main class="max-w-6xl mx-auto px-4 py-6">
    <router-view />
  </main>
</template>
