import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import FeatureA from '../views/FeatureA.vue'
import FeatureB from '../views/FeatureB.vue'
import FeatureC from '../views/FeatureC.vue'
import Profile from '../views/Profile.vue'
import Search from '../views/Search.vue'

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
      path: '/search',
      name: 'search',
      component: Search,
    },
  ],
})

export default router
