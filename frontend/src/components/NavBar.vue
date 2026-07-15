<script setup>
import api from '../api'
import { useAuthStore } from '../store'

const auth = useAuthStore()
</script>

<template>
  <nav class="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">
      <router-link to="/" class="font-bold text-lg tracking-tight">
        Wiki<span class="text-blue-600 dark:text-blue-400">STAR</span>
      </router-link>
      <div class="flex-1"></div>
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
