import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
const Reality = () => import('../views/Reality.vue')
const Forecast = () => import('../views/Forecast.vue')
const Mine = () => import('../views/Mine.vue')
const Radar = () => import('../views/Radar.vue')
const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')

const routes = [
    { path: '/feedback', component: () => import('../views/Feedback.vue') },

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
    },

    {
        path: '/email-setting',
        name: 'EmailSetting',
        component: () =>
            import('../views/EmailSetting.vue')
    }
]


const router=createRouter({

    history:createWebHistory(),

    routes

})


export default router
