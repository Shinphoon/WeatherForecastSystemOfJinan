<template>
<div class="app" @click="createConfetti">
    <router-view v-slot="{ Component }">
        <KeepAlive>
            <component :is="Component" />
        </KeepAlive>
    </router-view>

    <div class="bottom-nav">
        <router-link to="/" @click.stop="navEffect">
            <div class="nav-icon">🏠</div>
            <span>首页</span>
        </router-link>

        <router-link to="/reality" @click.stop="navEffect">
            <div class="nav-icon">🌡</div>
            <span>实况</span>
        </router-link>

        <router-link to="/forecast" @click.stop="navEffect">
            <div class="nav-icon">🌤</div>
            <span>预报</span>
        </router-link>

        <router-link to="/mine" @click.stop="navEffect">
            <div class="nav-icon">👤</div>
            <span>我的</span>
        </router-link>
    </div>

    <div
        v-for="ripple in ripples"
        :key="'r' + ripple.id"
        class="nav-ripple"
        :style="{
            left: ripple.x + 'px',
            top: ripple.y + 'px'
        }"
    ></div>

    <div
        v-for="item in confetti"
        :key="'c' + item.id"
        class="confetti"
        :style="{
            left: item.x + 'px',
            top: item.y + 'px',
            width: item.width + 'px',
            height: item.height + 'px',
            background: item.color,
            '--dx': item.dx + 'px',
            '--dy': item.dy + 'px',
            '--rotate': item.rotate + 'deg',
            '--duration': item.duration + 'ms'
        }"
    ></div>
</div>
</template>

<script setup>
import { ref } from 'vue'

const confetti = ref([])
const ripples = ref([])

let confettiId = 0
let rippleId = 0

function navEffect(event) {
    const target = event.currentTarget

    target.classList.remove('nav-glow')
    void target.offsetWidth
    target.classList.add('nav-glow')

    const rect = target.getBoundingClientRect()

    const ripple = {
        id: rippleId++,
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2
    }

    ripples.value.push(ripple)

    setTimeout(() => {
        ripples.value = ripples.value.filter(item => item.id !== ripple.id)
    }, 650)

    setTimeout(() => {
        target.classList.remove('nav-glow')
    }, 550)
}

function createConfetti(event) {
    const colors = [
        '#ff4d4f',
        '#ff9f1c',
        '#ffd60a',
        '#52c41a',
        '#00c2ff',
        '#1677ff',
        '#722ed1',
        '#eb2f96'
    ]

    for (let i = 0; i < 14; i++) {
        const id = confettiId++

        const item = {
            id,
            x: event.clientX + (Math.random() - 0.5) * 26,
            y: event.clientY + (Math.random() - 0.5) * 16,
            width: 5 + Math.random() * 6,
            height: 7 + Math.random() * 9,
            dx: (Math.random() - 0.5) * 170,
            dy: 140 + Math.random() * 150,
            rotate: (Math.random() - 0.5) * 1080,
            duration: 800 + Math.random() * 600,
            color: colors[Math.floor(Math.random() * colors.length)]
        }

        confetti.value.push(item)

        setTimeout(() => {
            confetti.value = confetti.value.filter(c => c.id !== id)
        }, item.duration + 100)
    }
}
</script>

<style scoped>
.app{
    min-height:100vh;
    padding-bottom:80px;
    overflow-x:hidden;
}

.bottom-nav{
    position:fixed;
    bottom:0;
    left:50%;
    transform:translateX(-50%);
    width:390px;
    height:70px;
    background:rgba(255,255,255,0.96);
    backdrop-filter:blur(16px);
    -webkit-backdrop-filter:blur(16px);
    border-radius:25px 25px 0 0;
    display:flex;
    justify-content:space-around;
    align-items:center;
    box-shadow:
        0 -3px 15px rgba(0,0,0,0.08),
        0 -1px 0 rgba(38,124,255,0.06);
    z-index:1000;
}

.bottom-nav a{
    position:relative;
    text-decoration:none;
    color:#777;
    width:70px;
    height:50px;
    border-radius:16px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    font-size:13px;
    transition:
        color .25s ease,
        background .25s ease,
        transform .2s ease,
        box-shadow .2s ease;
    -webkit-tap-highlight-color:transparent;
}

.bottom-nav a.router-link-active{
    background:linear-gradient(
        135deg,
        rgba(232,241,255,0.95),
        rgba(220,235,255,0.95)
    );
    color:#267cff;
    box-shadow:
        0 4px 12px rgba(38,124,255,0.12),
        inset 0 0 0 1px rgba(38,124,255,0.05);
}

.nav-icon{
    font-size:21px;
    line-height:21px;
    transition:transform .2s ease;
}

.bottom-nav span{
    margin-top:4px;
}

.bottom-nav a.nav-glow{
    animation:navGlow .55s ease;
}

.bottom-nav a.nav-glow .nav-icon{
    animation:iconBounce .55s ease;
}

.nav-ripple{
    position:fixed;
    width:16px;
    height:16px;
    border-radius:50%;
    pointer-events:none;
    z-index:999;
    background:rgba(38,124,255,0.38);
    transform:translate(-50%,-50%);
    animation:rippleExpand .65s ease-out forwards;
}

.confetti{
    position:fixed;
    border-radius:2px;
    pointer-events:none;
    z-index:9999;
    opacity:1;
    animation:confettiFall var(--duration) cubic-bezier(.18,.72,.32,1) forwards;
}

@keyframes navGlow{
    0%{
        transform:scale(1);
        box-shadow:0 0 0 rgba(38,124,255,0);
    }

    35%{
        transform:scale(1.1);
        box-shadow:
            0 0 10px rgba(38,124,255,0.9),
            0 0 22px rgba(38,124,255,0.6),
            0 0 38px rgba(38,124,255,0.35);
    }

    100%{
        transform:scale(1);
        box-shadow:0 0 0 rgba(38,124,255,0);
    }
}

@keyframes iconBounce{
    0%{
        transform:translateY(0) scale(1);
    }

    35%{
        transform:translateY(-4px) scale(1.16);
    }

    100%{
        transform:translateY(0) scale(1);
    }
}

@keyframes rippleExpand{
    0%{
        width:16px;
        height:16px;
        opacity:.7;
        box-shadow:0 0 12px rgba(38,124,255,.7);
    }

    100%{
        width:110px;
        height:110px;
        opacity:0;
        box-shadow:0 0 30px rgba(38,124,255,0);
    }
}

@keyframes confettiFall{
    0%{
        opacity:1;
        transform:
            translate(0,0)
            rotate(0deg)
            scale(1);
    }

    20%{
        opacity:1;
        transform:
            translate(
                calc(var(--dx) * .3),
                -25px
            )
            rotate(calc(var(--rotate) * .2))
            scale(1);
    }

    100%{
        opacity:0;
        transform:
            translate(
                var(--dx),
                var(--dy)
            )
            rotate(var(--rotate))
            scale(.75);
    }
}
</style>