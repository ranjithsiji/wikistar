<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-white sticky-top shadow-sm">
    <div class="container-xl">
      <!-- Brand -->
      <router-link class="navbar-brand d-flex align-items-center gap-2 fw-bold" to="/">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#0d6efd" stroke-width="2" stroke-linejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="#0d6efd" stroke-width="2" stroke-linejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="#0d6efd" stroke-width="2" stroke-linejoin="round"/>
        </svg>
        <span>WikiSTAR</span>
      </router-link>

      <!-- Mobile Toggle -->
      <button class="navbar-toggler border-0" type="button" @click="navOpen = !navOpen" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <!-- Nav Links -->
      <div class="collapse navbar-collapse" :class="{ show: navOpen }">
        <ul class="navbar-nav me-auto ms-4">
          <li class="nav-item">
            <router-link class="nav-link" to="/" exact-active-class="active">Home</router-link>
          </li>
          <li class="nav-item" v-if="store.user">
            <router-link class="nav-link" to="/create">Create Editathon</router-link>
          </li>
        </ul>

        <!-- Right Side -->
        <div class="d-flex align-items-center gap-3">
          <LanguageSwitcher />

          <!-- Logged In -->
          <div v-if="store.user" class="dropdown" ref="dropdownRef">
            <button
              class="btn btn-outline-secondary d-flex align-items-center gap-2 py-1 px-3"
              @click="isOpen = !isOpen"
              type="button"
            >
              <span class="avatar-circle">{{ store.user.username.charAt(0).toUpperCase() }}</span>
              <span class="d-none d-sm-inline fw-semibold" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                {{ store.user.username }}
              </span>
              <i class="bi bi-chevron-down small"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow-sm mt-1" :class="{ show: isOpen }">
              <li class="px-3 py-2 border-bottom">
                <small class="text-muted d-block">Signed in as</small>
                <strong class="small">{{ store.user.username }}</strong>
                <span class="badge ms-1 text-capitalize" :class="roleBadgeClass">{{ store.user.role }}</span>
              </li>
              <li>
                <router-link class="dropdown-item" to="/personal-cabinet" @click="isOpen = false">
                  <i class="bi bi-person-circle me-2"></i>Personal Cabinet
                </router-link>
              </li>
              <li v-if="store.user.role === 'admin'">
                <router-link class="dropdown-item" to="/admin" @click="isOpen = false">
                  <i class="bi bi-shield-lock me-2"></i>Admin Center
                </router-link>
              </li>
              <li v-if="store.user.role === 'admin' || store.user.role === 'jury'">
                <router-link class="dropdown-item" to="/personal-cabinet" @click="isOpen = false">
                  <i class="bi bi-check2-square me-2"></i>Approval Queue
                </router-link>
              </li>
              <li><hr class="dropdown-divider"></li>
              <li>
                <button class="dropdown-item text-danger" @click="handleLogout">
                  <i class="bi bi-box-arrow-right me-2"></i>Sign Out
                </button>
              </li>
            </ul>
          </div>

          <!-- Not Logged In -->
          <a v-else href="/api/login" class="btn btn-primary d-flex align-items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
              <polyline points="10,17 15,12 10,7"/>
              <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
            Sign in with Wikimedia
          </a>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
import { store, fetchCurrentUser, logout } from '../store'

const isOpen = ref(false)
const navOpen = ref(false)
const dropdownRef = ref(null)

const roleBadgeClass = computed(() => {
  if (!store.user) return ''
  const role = store.user.role
  if (role === 'admin') return 'bg-danger text-white'
  if (role === 'jury') return 'bg-warning text-dark'
  return 'bg-secondary text-white'
})

function handleLogout() {
  isOpen.value = false
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
.navbar {
  padding: 0.6rem 0;
  border-bottom: 1px solid #e9ecef;
  z-index: 1030;
}

.navbar-brand {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: -0.01em;
  text-decoration: none;
}

.navbar-brand:hover {
  color: #0d6efd;
}

.nav-link {
  font-weight: 500;
  color: #495057;
  transition: color 0.2s;
  padding: 0.5rem 0.75rem;
}

.nav-link:hover,
.nav-link.active {
  color: #0d6efd;
}

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
  z-index: 1050;
}

.dropdown-menu.show {
  display: block;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 0.55rem 1rem;
  font-size: 0.875rem;
  color: #212529;
  cursor: pointer;
  background: none;
  border: none;
  width: 100%;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}
</style>
