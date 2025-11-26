import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import CreateEditathon from './views/CreateEditathon.vue'
import EditathonDetail from './views/EditathonDetail.vue'
import JudgeView from './views/JudgeView.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/create', component: CreateEditathon },
  { path: '/editathon/:id', component: EditathonDetail, props: true },
  { path: '/editathon/:id/judge', component: JudgeView, props: true },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

export default createRouter({ history: createWebHistory(), routes })
