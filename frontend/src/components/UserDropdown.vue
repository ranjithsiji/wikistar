<template>
  <div v-if="store.user" class="dropdown">
    <button 
      class="btn btn-outline-secondary dropdown-toggle d-flex align-items-center gap-2" 
      @click="toggleDropdown" 
      type="button"
      id="userDropdown"
    >
      <span class="user-icon">👤</span>
      {{ store.user.username }}
    </button>
    <ul class="dropdown-menu dropdown-menu-end" v-show="isOpen" :class="{ show: isOpen }">
      <li>
        <router-link class="dropdown-item" to="/personal-cabinet" @click="closeDropdown">
          🏠 Personal Cabinet
        </router-link>
      </li>
      <li><hr class="dropdown-divider"></li>
      <li><button class="dropdown-item text-danger" @click="handleLogout">🚪 Log out</button></li>
    </ul>
  </div>
  <div v-else class="d-flex align-items-center gap-2">
    <div v-if="store.devMode" class="btn-group btn-group-sm border border-dashed p-1 bg-light rounded">
      <button class="btn btn-outline-primary btn-sm" @click="handleDevLogin('admin')">Dev Admin</button>
      <button class="btn btn-outline-primary btn-sm" @click="handleDevLogin('jury')">Dev Jury</button>
      <button class="btn btn-outline-primary btn-sm" @click="handleDevLogin('participant')">Dev User</button>
    </div>
    <button class="btn btn-primary" @click="redirectToLogin">
      Login
    </button>
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

function handleLogout() {
  closeDropdown()
  logout()
}

function redirectToLogin() {
  window.location.href = '/api/login'
}

function handleDevLogin(role) {
  window.location.href = `/api/dev-login/${role}`
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
  display: none;
  min-width: 180px;
  background-color: #fff;
  border: 1px solid rgba(0,0,0,.15);
  border-radius: .375rem;
  box-shadow: 0 .5rem 1rem rgba(0,0,0,.15);
}

.dropdown-menu.show {
  display: block;
}

.border-dashed {
  border-style: dashed !important;
}
</style>
