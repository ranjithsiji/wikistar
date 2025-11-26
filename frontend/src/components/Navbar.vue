<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
    <div class="container container-max">
      <router-link class="navbar-brand fw-bold" to="/">✏️ Editathons</router-link>
      <div class="d-flex align-items-center ms-auto">
        <LanguageSwitcher />
        <UserDropdown />
      </div>
    </div>
  </nav>
</template>

<script setup>
import LanguageSwitcher from './LanguageSwitcher.vue'
import UserDropdown from './UserDropdown.vue'
</script>
