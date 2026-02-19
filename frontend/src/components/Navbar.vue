<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
    <div class="container container-max">
      <router-link class="navbar-brand fw-bold" to="/">✏️ WikiSTAR</router-link>
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

<style scoped>
.navbar {
  padding: 1rem 0;
  border-bottom: 1px solid #e5e5e5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-brand {
  font-size: 1.25rem;
  font-weight: 700;
  color: #333;
  text-decoration: none;
}

.navbar-brand:hover {
  color: #0645ad;
}

.d-flex {
  display: flex;
  gap: 15px;
}

.align-items-center {
  align-items: center;
}

.ms-auto {
  margin-left: auto;
}

.bg-white {
  background-color: #fff;
}

.shadow-sm {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}
</style>
