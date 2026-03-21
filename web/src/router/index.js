import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import DiscoveryHome from '../views/DiscoveryHome.vue'
import DataAnalysisAndVisualization from '../views/DataAnalysisAndVisualization.vue'
import History from '../views/History.vue'
import Favorites from '../views/Favorites.vue'
import Profile from '../views/Profile.vue'
import Search from '../views/Search.vue'
import Rewrite from '../views/Rewrite.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Settings from '../views/Settings.vue'
import TodoList from '../views/TodoList.vue'
import Admin from '../views/Admin.vue'
import Agent from '../views/Agent.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/discovery-home', name: 'discovery-home', component: DiscoveryHome },
    { path: '/data-analysis-and-visualization', name: 'data-analysis-and-visualization', component: DataAnalysisAndVisualization },
    { path: '/history', name: 'history', component: History },
    { path: '/favorites', name: 'favorites', component: Favorites },
    { path: '/profile', name: 'profile', component: Profile },
    { path: '/settings', name: 'settings', component: Settings },
    { path: '/search', name: 'search', component: Search },
    { path: '/rewrite', name: 'rewrite', component: Rewrite },
    { path: '/login', name: 'login', component: Login },
    { path: '/register', name: 'register', component: Register },
    { path: '/todo', name: 'todo', component: TodoList },
    { path: '/admin', name: 'admin', component: Admin },
    { path: '/agent', name: 'agent', component: Agent },
  ],
})

export default router
