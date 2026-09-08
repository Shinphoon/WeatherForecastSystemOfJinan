<template>
  <div class="mine-page">
    <header class="page-header">
      <div>
        <h1>个人中心</h1>
        <p>账号信息 · 天气偏好 · 系统设置</p>
      </div>
      <div class="setting-icon">⚙</div>
    </header>

    <section v-if="loading" class="login-card">
    <div class="login-content">
        <div class="login-title">正在读取账号信息...</div>
    </div>
    </section>

    <section v-if="isLoggedIn" class="profile-card">
      <div class="avatar">
        {{ avatarText }}
      </div>
      <div class="profile-main">
        <div class="nickname">{{ user.nickname || '天气用户' }}</div>
        <div class="username">@{{ user.username }}</div>
        <div class="user-tags">
          <span>济南天气用户</span>
          <span>ID {{ user.id || '--' }}</span>
        </div>
      </div>
      <button class="edit-btn">编辑</button>
    </section>

    <section v-else class="login-card">
      <div class="login-icon">👤</div>
      <div class="login-content">
        <div class="login-title">登录你的天气账号</div>
        <div class="login-desc">登录后可保存默认气象站、位置和预警设置</div>
      </div>
      <router-link to="/login" class="login-btn">登录</router-link>
    </section>

    <section class="section">
      <div class="section-title">天气偏好</div>
      <div class="menu-card">
        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">📍</div>
            <div>
              <div class="menu-name">默认气象站</div>
              <div class="menu-desc">首页、实况和预报默认显示</div>
            </div>
          </div>
          <div class="menu-right">{{ selectedStationName }} ›</div>
        </div>

        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">🔔</div>
            <div>
              <div class="menu-name">天气预警推送</div>
              <div class="menu-desc">接收济南市气象预警信息</div>
            </div>
          </div>
          <label class="switch">
            <input v-model="pushEnabled" type="checkbox">
            <span class="slider"></span>
          </label>
        </div>

        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">📡</div>
            <div>
              <div class="menu-name">雷达图层</div>
              <div class="menu-desc">默认开启雷达回波显示</div>
            </div>
          </div>
          <label class="switch">
            <input v-model="radarEnabled" type="checkbox">
            <span class="slider"></span>
          </label>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-title">账号与位置</div>
      <div class="menu-card">
        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">📱</div>
            <div>
              <div class="menu-name">手机号</div>
              <div class="menu-desc">{{ maskedPhone }}</div>
            </div>
          </div>
          <div class="arrow">›</div>
        </div>

        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">🗺</div>
            <div>
              <div class="menu-name">最近位置</div>
              <div class="menu-desc">{{ user.last_address || '暂未记录位置' }}</div>
            </div>
          </div>
          <div class="arrow">›</div>
        </div>

        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">🔐</div>
            <div>
              <div class="menu-name">账号安全</div>
              <div class="menu-desc">修改密码与登录信息</div>
            </div>
          </div>
          <div class="arrow">›</div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-title">系统</div>
      <div class="menu-card">
        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">ℹ️</div>
            <div>
              <div class="menu-name">关于系统</div>
              <div class="menu-desc">济南市天气实况与天气预报可视化系统</div>
            </div>
          </div>
          <div class="arrow">›</div>
        </div>

        <div class="menu-item">
          <div class="menu-left">
            <div class="menu-icon">💬</div>
            <div>
              <div class="menu-name">意见反馈</div>
              <div class="menu-desc">课程设计演示功能</div>
            </div>
          </div>
          <div class="arrow">›</div>
        </div>
      </div>
    </section>

    <button v-if="isLoggedIn" class="logout-btn" @click="logout">
      退出登录
    </button>

    <div class="version">济南天气 · WebGIS Course Design v1.0</div>
    <div class="bottom-space"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser } from '../api/auth'

const router = useRouter()
const loading = ref(true)
const isLoggedIn = ref(false)
const user = ref({
  id:'',
  username:'',
  nickname:'',
  phone:'',
  avatar:'',
  last_address:'',
  push_enable:1,
  create_time:''
})

const stationOptions = [
  { id:'54823', name:'济南' },
  { id:'54727', name:'章丘' },
  { id:'54816', name:'长清' },
  { id:'54818', name:'平阴' },
  { id:'54821', name:'济阳' },
  { id:'54828', name:'莱芜' }
]

const selectedStationId = ref(
  localStorage.getItem('selectedStationId') || '54823'
)

const selectedStationName = computed(() => {
  const station = stationOptions.find(
    item => item.id === selectedStationId.value
  )
  return station ? station.name : '济南'
})

const avatarText = computed(() => {
  const text =
    user.value.nickname ||
    user.value.username ||
    '天'
  return text.slice(0,1)
})

const maskedPhone = computed(() => {
  const phone = user.value.phone
  if (!phone) return '未绑定手机号'
  if (phone.length !== 11) return phone
  return `${phone.slice(0,3)}****${phone.slice(7)}`
})

const pushEnabled = ref(true)
const radarEnabled = ref(
  localStorage.getItem('radarEnabled') !== 'false'
)

async function loadUser() {
  const token =
    localStorage.getItem('access_token')

  if (!token) {
    loading.value = false
    isLoggedIn.value = false
    return
  }

  try {
    const response =
      await getCurrentUser()

    user.value = response.data
    isLoggedIn.value = true

    pushEnabled.value =
      response.data.push_enable !== 0

  } catch (err) {
    console.error(
      '获取用户信息失败：',
      err
    )

    localStorage.removeItem(
      'access_token'
    )

    localStorage.removeItem(
      'user'
    )

    isLoggedIn.value = false
  } finally {
    loading.value = false
  }
}

function logout() {
  localStorage.removeItem(
    'access_token'
  )
  localStorage.removeItem(
    'user'
  )
  localStorage.removeItem(
    'demoLogin'
  )
  localStorage.removeItem(
    'demoUsername'
  )

  isLoggedIn.value = false

  router.push('/login')
}

onMounted(loadUser)
</script>

<style scoped>
.mine-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 22px 16px 110px;
  background: linear-gradient(180deg,#e7f1ff 0%,#f4f7fb 320px,#f5f7fa 100%);
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: #1e293b;
}
.page-header p {
  margin: 6px 0 0;
  font-size: 12px;
  color: #94a3b8;
}
.setting-icon {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: white;
  font-size: 20px;
  box-shadow: 0 5px 15px rgba(15,23,42,.06);
}
.profile-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  margin-bottom: 24px;
  border-radius: 24px;
  background: white;
  box-shadow: 0 8px 24px rgba(15,23,42,.07);
}
.avatar {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 20px;
  background: linear-gradient(135deg,#5d86ff,#3b70ff);
  color: white;
  font-size: 26px;
  font-weight: 700;
}
.profile-main {
  flex: 1;
  min-width: 0;
}
.nickname {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}
.username {
  margin-top: 3px;
  font-size: 12px;
  color: #94a3b8;
}
.user-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 9px;
}
.user-tags span {
  padding: 4px 7px;
  border-radius: 8px;
  background: #eef4ff;
  color: #4b7cff;
  font-size: 10px;
}
.edit-btn {
  padding: 7px 11px;
  border: none;
  border-radius: 11px;
  background: #edf4ff;
  color: #3970ff;
  cursor: pointer;
}
.login-card {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 20px;
  margin-bottom: 24px;
  border-radius: 24px;
  background: white;
  box-shadow: 0 8px 24px rgba(15,23,42,.07);
}
.login-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 16px;
  background: #edf4ff;
  font-size: 23px;
}
.login-content {
  flex: 1;
}
.login-title {
  font-size: 15px;
  font-weight: 700;
  color: #334155;
}
.login-desc {
  margin-top: 5px;
  font-size: 10px;
  line-height: 1.5;
  color: #94a3b8;
}
.login-btn {
  padding: 8px 13px;
  border-radius: 12px;
  background: #4b7cff;
  color: white;
  font-size: 12px;
  text-decoration: none;
}
.section {
  margin-bottom: 23px;
}
.section-title {
  margin: 0 4px 10px;
  font-size: 15px;
  font-weight: 700;
  color: #334155;
}
.menu-card {
  overflow: hidden;
  border-radius: 20px;
  background: white;
  box-shadow: 0 6px 18px rgba(15,23,42,.05);
}
.menu-item {
  min-height: 67px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 15px;
  border-bottom: 1px solid #f1f5f9;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-left {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
}
.menu-icon {
  width: 37px;
  height: 37px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 11px;
  background: #f1f5fb;
  font-size: 17px;
}
.menu-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}
.menu-desc {
  max-width: 245px;
  margin-top: 4px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 10px;
  color: #94a3b8;
}
.menu-right,
.arrow {
  margin-left: 10px;
  flex-shrink: 0;
  font-size: 12px;
  color: #94a3b8;
}
.arrow {
  font-size: 20px;
}
.switch {
  position: relative;
  width: 43px;
  height: 24px;
  flex-shrink: 0;
}
.switch input {
  display: none;
}
.slider {
  position: absolute;
  inset: 0;
  border-radius: 20px;
  background: #dbe3ed;
  cursor: pointer;
  transition: .2s;
}
.slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  border-radius: 50%;
  background: white;
  transition: .2s;
  box-shadow: 0 1px 4px rgba(0,0,0,.15);
}
.switch input:checked + .slider {
  background: #4b7cff;
}
.switch input:checked + .slider::before {
  transform: translateX(19px);
}
.logout-btn {
  width: 100%;
  height: 48px;
  margin-top: 4px;
  border: none;
  border-radius: 15px;
  background: white;
  color: #ef4444;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(15,23,42,.05);
}
.version {
  margin-top: 22px;
  text-align: center;
  color: #b0bac8;
  font-size: 10px;
}
.bottom-space {
  height: 20px;
}
</style>