import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Reality from '../views/Reality.vue'
import Forecast from '../views/Forecast.vue'
import Mine from '../views/Mine.vue'
import Radar from '../views/Radar.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'

const routes = [

    {
        path: '/',
        name:'Home',
        component:Home
    },

    {
        path:'/reality',
        name:'Reality',
        component:Reality
    },

    {
        path:'/forecast',
        name:'Forecast',
        component:Forecast
    },

    {
        path:'/mine',
        name:'Mine',
        component:Mine
    },

    {
        path: '/radar',
        name: 'Radar',
        component: Radar
    },

    {
        path: '/login',
        name: 'Login',
        component: Login
    },

    {
        path: '/register',
        name: 'Register',
        component: Register
    },

    {
        path: '/security',
        name: 'Security',
        component: () => import('../views/Security.vue')
    },

    {
        path: '/phone-setting',
        name: 'PhoneSetting',
        component: () => import('../views/PhoneSetting.vue')
    },

    {
        path: '/location-setting',
        name: 'LocationSetting',
        component: () => import('../views/LocationSetting.vue')
    },

    {
        path: '/wechat-admin',
        name: 'WechatAdmin',
        component: () => import('../views/WechatAdmin.vue')
    }
]


const router=createRouter({

    history:createWebHistory(),

    routes

})


export default router