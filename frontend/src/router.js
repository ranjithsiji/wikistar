import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './store'

// The single router of the app (v1 had two competing ones).
const routes = [
  { path: '/', name: 'home', component: () => import('./views/HomeView.vue') },
  { path: '/contests', name: 'contests', component: () => import('./views/ContestsView.vue') },
  { path: '/campaigns/new', name: 'campaign-create', component: () => import('./views/CampaignFormView.vue'), meta: { requiresAuth: true } },
  // :tab is constrained to the known tab keys so it can never shadow
  // /judge or /edit below (those stay separate routes/components).
  {
    path: '/campaigns/:slug/:tab(overview|submissions|suggested|leaderboard|rules|stats)?',
    name: 'campaign', component: () => import('./views/CampaignView.vue'), props: true
  },
  { path: '/campaigns/:slug/judge', name: 'campaign-judge', component: () => import('./views/JudgeView.vue'), props: true, meta: { requiresAuth: true } },
  { path: '/campaigns/:slug/edit', name: 'campaign-edit', component: () => import('./views/CampaignFormView.vue'), props: true, meta: { requiresAuth: true } },
  { path: '/admin', name: 'admin', component: () => import('./views/AdminView.vue'), meta: { requiresAdmin: true } },
  { path: '/dashboard', name: 'dashboard', component: () => import('./views/DashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/preferences', name: 'preferences', component: () => import('./views/PreferencesView.vue'), meta: { requiresAuth: true } },
  { path: '/about', name: 'about', component: () => import('./views/AboutView.vue') }
]

const router = createRouter({ history: createWebHistory(), routes })

// Client-side guard: keep logged-out / non-admin users out of the pages
// that only render errors for them anyway (the backend is the real
// enforcer; this just avoids leaking the UI and firing doomed API calls).
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth && !to.meta.requiresAdmin) return true
  const auth = useAuthStore()
  if (!auth.loaded) await auth.fetchUser()
  if (!auth.isLoggedIn) return { path: '/', query: { login: '1' } }
  if (to.meta.requiresAdmin && !auth.isAdmin) return { path: '/' }
  return true
})

export default router
