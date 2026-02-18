import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import CreateEditathon from './views/CreateEditathon.vue'
import EditathonDashboard from './views/EditathonDashboard.vue'
import PersonalCabinet from './views/PersonalCabinet.vue'
import JudgeView from './views/JudgeView.vue'
import JuryViewFullScreen from './views/JuryViewFullScreen.vue'
import JuryArticlesFullScreen from './views/JuryArticlesFullScreen.vue'
import ArticleReviewFullScreen from './views/ArticleReviewFullScreen.vue'
import SubmitArticle from './views/SubmitArticle.vue'
import EditEditathon from './views/EditEditathon.vue'
import { store, fetchCurrentUser } from './store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/create',
    name: 'CreateEditathon',
    component: CreateEditathon,
    meta: { requiresAuth: true }
  },
  {
    path: '/editathon/:id',
    name: 'EditathonDashboard',
    component: EditathonDashboard,
    props: true
  },
  {
    path: '/editathon/:id/judge',
    name: 'JudgeView',
    component: JudgeView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/editathon/:id/jury',
    name: 'JuryViewFullScreen',
    component: JuryViewFullScreen,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/editathon/:id/articles',
    name: 'JuryArticlesFullScreen',
    component: JuryArticlesFullScreen,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/editathon/:id/review',
    name: 'ArticleReviewFullScreen',
    component: ArticleReviewFullScreen,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/editathon/:id/submit',
    name: 'SubmitArticle',
    component: SubmitArticle,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/editathon/:id/edit',
    name: 'EditEditathon',
    component: EditEditathon,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/personal-cabinet',
    name: 'PersonalCabinet',
    component: PersonalCabinet,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard to check authentication
router.beforeEach(async (to, from, next) => {
  // Wait for auth check to complete on first navigation
  if (!store.isAuthChecked) {
    await fetchCurrentUser()
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (!store.user) {
      // Redirect to login
      window.location.href = '/api/login'
      return
    }
  }

  next()
})

export default router