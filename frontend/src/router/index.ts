import {createRouter, createWebHistory, type Router, type RouteRecordRaw} from 'vue-router'

// Define routes
const routes: RouteRecordRaw[] = [
    {
        path: '/',
        name: 'Home',
        component: () => import('../views/Home.vue')
    },
    {
        path: '/about',
        name: 'About',
        component: () => import('../views/About.vue')
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/LoginPage.vue'),
        meta: {
          requiresAuth: false,
          title: 'Login - Routine Cloud'
        }
    },
    {
        path: '/oauth/authorize',
        name: 'OAuthAuthorize',
        component: () => import('../views/OAuthAuthorize.vue'),
        meta: {
          title: 'Link Alexa - Routine Cloud'
        }
    },
    {
        path: '/routines',
        name: 'Routines',
        component: () => import('../views/RoutinesPage.vue'),
        meta: { title: 'Routines - Routine Cloud' }
    },
    {
        path: '/routines/:id',
        name: 'RoutineDetail',
        component: () => import('../views/RoutineDetailPage.vue'),
        meta: { title: 'Routine - Routine Cloud' }
    },
    {
        path: '/tasks',
        name: 'Tasks',
        component: () => import('../views/TaskLibraryPage.vue'),
        meta: { title: 'Tasks - Routine Cloud' }
    },
    {
        path: '/device',
        name: 'DeviceVerify',
        component: () => import('../views/DeviceVerifyPage.vue'),
        meta: { title: 'Link Device - Routine Cloud' }
    },
    {
        path: '/callback',
        name: 'OAuthCallback',
        component: () => import('../views/CallbackPage.vue'),
        meta: { title: 'Logging in... - Routine Cloud' }
    },
    {
        path: "/konto",
        name: "Konto",
        component: () => import("../views/KontoPage.vue"),
        meta: { title: "Konto - Routine Cloud" }
    },
    {
        path: "/admin",
        name: "Admin",
        component: () => import("../views/AdminPage.vue"),
        meta: { title: "Admin - Routine Cloud" }
    }
]

// Create router instance
const router: Router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes
})

// Navigation guards
router.beforeEach((to, _from, next) => {
  // Update document title
  const meta: any = (to as any).meta || {}
  document.title = meta.title || 'Routine Cloud'

  next()
})

export default router
