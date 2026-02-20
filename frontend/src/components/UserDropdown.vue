<template>
  <!-- Logged In State -->
  <div v-if="store.user" class="dropdown" ref="dropdownRef">
    <button
      class="btn btn-outline-secondary d-flex align-items-center gap-2 py-1 px-3"
      @click="isOpen = !isOpen"
      type="button"
    >
      <span class="avatar-circle">{{ store.user.username.charAt(0).toUpperCase() }}</span>
      <span class="d-none d-sm-inline fw-semibold username-text">
        {{ store.user.username }}
      </span>
      <i class="bi bi-chevron-down small"></i>
    </button>

    <ul class="dropdown-menu dropdown-menu-end shadow mt-1" :class="{ show: isOpen }">
      <li class="px-3 py-2 border-bottom">
        <small class="text-muted d-block">Signed in as</small>
        <strong class="small">{{ store.user.username }}</strong>
        <span class="badge ms-1 text-capitalize" :class="roleBadgeClass">{{ store.user.role }}</span>
      </li>
      <li>
        <router-link class="dropdown-item" to="/personal-cabinet" @click="closeDropdown">
          <i class="bi bi-person-circle me-2"></i>Personal Cabinet
        </router-link>
      </li>
      <li><hr class="dropdown-divider"></li>
      <li>
        <button class="dropdown-item text-danger w-100" @click="handleLogout">
          <i class="bi bi-box-arrow-right me-2"></i>Sign Out
        </button>
      </li>
    </ul>
  </div>

  <!-- Logged Out State -->
  <a v-else href="/api/login" class="btn btn-primary d-flex align-items-center gap-2">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
      <polyline points="10,17 15,12 10,7"/>
      <line x1="15" y1="12" x2="3" y2="12"/>
    </svg>
    Sign in
  </a>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { store, fetchCurrentUser, logout } from '../store'

const isOpen = ref(false)
const dropdownRef = ref(null)

const roleBadgeClass = computed(() => {
  if (!store.user) return ''
  const role = store.user.role
  if (role === 'admin') return 'bg-danger text-white'
  if (role === 'jury') return 'bg-warning text-dark'
  return 'bg-secondary text-white'
})

function closeDropdown() {
  isOpen.value = false
}

function handleLogout() {
  closeDropdown()
  logout()
}

function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
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
.avatar-circle {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #0d6efd, #6610f2);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.username-text {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  left: auto;
  display: none;
  min-width: 220px;
  background: #fff;
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 10px;
  overflow: hidden;
  z-index: 2000;
  padding: 0;
}

.dropdown-menu.show {
  display: block;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 0.6rem 1rem;
  font-size: 0.875rem;
  color: #212529;
  cursor: pointer;
  background: none;
  border: none;
  width: 100%;
  text-decoration: none;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}
</style>
