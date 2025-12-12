import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import CreateEditathon from './views/CreateEditathon.vue'
import EditathonDashboard from './views/EditathonDashboard.vue'
import PersonalCabinet from './views/PersonalCabinet.vue'
import JudgeView from './views/JudgeView.vue'
import JuryViewFullScreen from './views/JuryViewFullScreen.vue'
import JuryArticlesFullScreen from './views/JuryArticlesFullScreen.vue'
import ArticleReviewFullScreen from './views/ArticleReviewFullScreen.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/create',
    name: 'CreateEditathon',
    component: CreateEditathon
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
    props: true
  },
  {
    path: '/editathon/:id/jury',
    name: 'JuryViewFullScreen',
    component: JuryViewFullScreen,
    props: true
  },
  {
    path: '/editathon/:id/articles',
    name: 'JuryArticlesFullScreen',
    component: JuryArticlesFullScreen,
    props: true
  },
  {
    path: '/editathon/:id/review',
    name: 'ArticleReviewFullScreen',
    component: ArticleReviewFullScreen,
    props: true
  },
  {
    path: '/personal-cabinet',
    name: 'PersonalCabinet',
    component: PersonalCabinet
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router