import { createRouter, createWebHistory } from 'vue-router'

// The single router of the app (v1 had two competing ones).
const routes = [
  { path: '/', name: 'home', component: () => import('./views/HomeView.vue') },
  { path: '/campaigns/new', name: 'campaign-create', component: () => import('./views/CampaignFormView.vue') },
  { path: '/campaigns/:slug', name: 'campaign', component: () => import('./views/CampaignView.vue'), props: true },
  { path: '/campaigns/:slug/edit', name: 'campaign-edit', component: () => import('./views/CampaignFormView.vue'), props: true },
  { path: '/admin', name: 'admin', component: () => import('./views/AdminView.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('./views/DashboardView.vue') },
  { path: '/preferences', name: 'preferences', component: () => import('./views/PreferencesView.vue') },
  { path: '/about', name: 'about', component: () => import('./views/AboutView.vue') }
]

export default createRouter({ history: createWebHistory(), routes })
