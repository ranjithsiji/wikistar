<script setup>
import api from '../api'
import { useAuthStore } from '../store'

const auth = useAuthStore()
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
      <router-link class="navbar-brand fw-bold" to="/">WikiSTAR</router-link>
      <div class="navbar-nav ms-auto align-items-center">
        <router-link class="nav-link" to="/campaigns/new" v-if="auth.isLoggedIn">
          Create campaign
        </router-link>
        <router-link class="nav-link" to="/admin" v-if="auth.isAdmin">Admin</router-link>
        <span class="navbar-text me-2" v-if="auth.isLoggedIn">{{ auth.user.username }}</span>
        <a class="btn btn-outline-light btn-sm" :href="api.logoutUrl" v-if="auth.isLoggedIn">Logout</a>
        <a class="btn btn-light btn-sm" :href="api.loginUrl" v-else>Login with Wikimedia</a>
      </div>
    </div>
  </nav>
</template>
