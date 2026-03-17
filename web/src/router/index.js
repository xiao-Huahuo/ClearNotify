import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import FeatureA from '../views/FeatureA.vue'
import FeatureB from '../views/FeatureB.vue'
import FeatureC from '../views/FeatureC.vue'
import Profile from '../views/Profile.vue'
import Search from '../views/Search.vue'
import Rewrite from '../views/Rewrite.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/feature-a',
      name: 'feature-a',
      component: FeatureA,
    },
    {
      path: '/feature-b',
      name: 'feature-b',
      component: FeatureB,
    },
    {
      path: '/feature-c',
      name: 'feature-c',
      component: FeatureC,
    },
    {
      path: '/profile',
      name: 'profile',
      component: Profile,
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
    },
    {
      path: '/search',
      name: 'search',
      component: Search,
    },
    {
      path: '/rewrite',
      name: 'rewrite',
      component: Rewrite,
    },
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/register',
      name: 'register',
      component: Register,
    }
  ],
})

export default router
