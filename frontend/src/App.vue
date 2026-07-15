<script setup>
import { onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import { useAuthStore } from './store'

const auth = useAuthStore()
onMounted(() => auth.fetchUser())
</script>

<template>
  <NavBar />
  <main class="container py-4">
    <router-view />
  </main>
</template>
