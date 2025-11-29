import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import CreateEditathon from './views/CreateEditathon.vue'
import EditathonDashboard from './views/EditathonDashboard.vue' // ✅ CHANGED
import JudgeView from './views/JudgeView.vue'
import PersonalCabinet from './views/PersonalCabinet.vue'

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
    name: 'EditathonDashboard', // ✅ CHANGED
    component: EditathonDashboard, // ✅ CHANGED
    props: true
  },
  {
    path: '/editathon/:id/judge',
    name: 'JudgeView',
    component: JudgeView,
    props: true
  },
  {
    path: '/personal-cabinet',
    name: 'PersonalCabinet',
    component: PersonalCabinet
  },
  {
    path: '/wiki-user-inspector',
    name: 'WikiUserInspector',
    component: WikiUserInspector
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router