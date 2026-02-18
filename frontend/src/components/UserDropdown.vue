<template>
  <div v-if="store.user" class="dropdown">
    <button class="btn btn-outline-secondary dropdown-toggle" @click="toggleDropdown" type="button">
      👤 {{ store.user.username }}
    </button>
    <ul class="dropdown-menu dropdown-menu-end" v-show="isOpen" :class="{ show: isOpen }">
      <li>
        <router-link class="dropdown-item" to="/personal-cabinet" @click="closeDropdown">
          🏠 Personal Cabinet
        </router-link>
      </li>
      <li><hr class="dropdown-divider"></li>
      <li><a class="dropdown-item text-danger" href="#" @click="handleLogout">🚪 Log out</a></li>
    </ul>
  </div>
  <div v-else>
    <a href="/api/login" class="btn btn-primary btn-sm">Login</a>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { store, fetchCurrentUser, logout } from '../store'

const isOpen = ref(false)

function toggleDropdown(event) {
  event.stopPropagation()
  isOpen.value = !isOpen.value
}

function closeDropdown() {
  isOpen.value = false
}

function handleLogout(event) {
  event.preventDefault()
  closeDropdown()
  logout()
}

function handleClickOutside(event) {
  const dropdown = event.target.closest('.dropdown')
  if (!dropdown) {
    isOpen.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  if (!store.isAuthChecked) {
    await fetchCurrentUser()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.dropdown {
  position: relative;
  z-index: 2000;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 2001;
  min-width: 180px;
  padding: 0.5rem 0;
  margin: 0.125rem 0 0;
  font-size: 1rem;
  color: #212529;
  text-align: left;
  list-style: none;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.375rem 1.5rem;
  clear: both;
  font-weight: 400;
  color: #212529;
  text-align: inherit;
  text-decoration: none;
  white-space: nowrap;
  background-color: transparent;
  border: 0;
  cursor: pointer;
}

.dropdown-item:hover {
  color: #1e2125;
  background-color: #f8f9fa;
}

.dropdown-divider {
  height: 0;
  margin: 0.5rem 0;
  overflow: hidden;
  border-top: 1px solid #e9ecef;
}

.btn {
  display: inline-block;
  font-weight: 400;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
  user-select: none;
  border: 1px solid transparent;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: 0.375rem;
  transition: all 0.15s ease-in-out;
  cursor: pointer;
  background-color: transparent;
}

.btn-outline-secondary {
  color: #6c757d;
  border-color: #6c757d;
}

.btn-outline-secondary:hover,
.btn-outline-secondary:focus {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.btn-primary {
  color: #fff;
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  color: #fff;
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  border-radius: 0.2rem;
}

.dropdown-toggle::after {
  display: inline-block;
  margin-left: 0.5em;
  vertical-align: 0.255em;
  content: "";
  border-top: 0.3em solid;
  border-right: 0.3em solid transparent;
  border-bottom: 0;
  border-left: 0.3em solid transparent;
}

.dropdown-menu.show {
  display: block;
}
</style>
