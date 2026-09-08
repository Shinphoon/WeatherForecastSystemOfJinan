<template>
  <div class="auth-page">
    <div class="auth-shell">
      <div class="brand">
        <div class="brand-icon">☁️</div>
        <h1>拾风观象台—济南天气</h1>
        <p>天气实况 · 天气预报 · 气象预警</p>
      </div>
      <div class="auth-card">
        <div class="card-title">
          <h2>欢迎回来</h2>
          <p>登录后可保存默认气象站和个人设置</p>
        </div>
        <form @submit.prevent="handleLogin">
          <div class="form-item">
            <label>用户名</label>
            <input v-model.trim="form.username" type="text" placeholder="请输入用户名">
          </div>
          <div class="form-item">
            <label>密码</label>
            <div class="password-box">
              <input v-model="form.password" :type="showPassword ? 'text' : 'password'" placeholder="请输入密码">
              <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>
          <div class="form-item">
            <label>验证码</label>
            <div class="captcha-row">
              <input v-model.trim="form.captcha" type="text" maxlength="4" placeholder="输入验证码">
              <button type="button" class="captcha" @click="refreshCaptcha">{{ captcha }}</button>
            </div>
          </div>
          <div v-if="errorText" class="error-text">{{ errorText }}</div>
          <button
            class="primary-btn"
            type="submit"
            :disabled="submitting"
            >
            {{ submitting ? '正在登录...' : '登录' }}
          </button>
        </form>
        <div class="switch-text">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
        <router-link to="/" class="back-home">先看看天气 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { loginUser } from '../api/auth'

const router = useRouter()
const showPassword = ref(false)
const captcha = ref('')
const errorText = ref('')
const submitting = ref(false)

const form = reactive({
  username: '',
  password: '',
  captcha: ''
})

function refreshCaptcha() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let result = ''
  for (let i = 0; i < 4; i++) {
    result += chars[Math.floor(Math.random() * chars.length)]
  }
  captcha.value = result
}

async function handleLogin() {
  errorText.value = ''

  if (!form.username) {
    errorText.value = '请输入用户名'
    return
  }

  if (!form.password) {
    errorText.value = '请输入密码'
    return
  }

  if (!form.captcha) {
    errorText.value = '请输入验证码'
    return
  }

  if (form.captcha.toUpperCase() !== captcha.value) {
    errorText.value = '验证码错误'
    form.captcha = ''
    refreshCaptcha()
    return
  }

  submitting.value = true

  try {
    const response = await loginUser({
      username: form.username,
      password: form.password
    })

    // 清理以前的演示登录字段
    localStorage.removeItem('demoLogin')
    localStorage.removeItem('demoUsername')
    localStorage.removeItem('demoNickname')
    localStorage.removeItem('demoPhone')

    // 保存真实 JWT
    localStorage.setItem(
      'access_token',
      response.data.access_token
    )

    // 保存后端返回的真实用户基础信息
    localStorage.setItem(
      'user',
      JSON.stringify(response.data.user)
    )

    // 登录成功后进入个人中心
    router.push('/mine')

  } catch (err) {
    console.error('登录失败：', err)

    if (err.response?.data?.detail) {
      errorText.value = err.response.data.detail
    } else {
      errorText.value = '登录失败，请稍后重试'
    }

    form.captcha = ''
    refreshCaptcha()

  } finally {
    submitting.value = false
  }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  padding: 32px 16px;
  background: linear-gradient(180deg,#dcecff 0%,#eef5ff 42%,#f7f9fc 100%);
}
.auth-shell {
  width: 100%;
  max-width: 430px;
}
.brand {
  padding: 24px 8px 28px;
  text-align: center;
}
.brand-icon {
  margin-bottom: 8px;
  font-size: 44px;
}
.brand h1 {
  margin: 0;
  font-size: 28px;
  color: #1e293b;
}
.brand p {
  margin: 8px 0 0;
  font-size: 13px;
  color: #64748b;
}
.auth-card {
  padding: 26px 22px;
  border-radius: 26px;
  background: rgba(255,255,255,.96);
  box-shadow: 0 14px 40px rgba(51,65,85,.12);
}
.card-title h2 {
  margin: 0;
  font-size: 24px;
  color: #1e293b;
}
.card-title p {
  margin: 7px 0 22px;
  font-size: 12px;
  color: #94a3b8;
}
.form-item {
  margin-bottom: 17px;
}
.form-item label {
  display: block;
  margin-bottom: 7px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}
.form-item input {
  width: 100%;
  height: 46px;
  box-sizing: border-box;
  padding: 0 13px;
  border: 1px solid #dbe4ef;
  border-radius: 13px;
  outline: none;
  background: #f8fafc;
  font-size: 14px;
  transition: .2s;
}
.form-item input:focus {
  border-color: #4b7cff;
  background: white;
  box-shadow: 0 0 0 3px rgba(75,124,255,.08);
}
.password-box {
  position: relative;
}
.password-box input {
  padding-right: 58px;
}
.eye-btn {
  position: absolute;
  top: 50%;
  right: 11px;
  transform: translateY(-50%);
  border: none;
  background: transparent;
  color: #4b7cff;
  font-size: 12px;
  cursor: pointer;
}
.captcha-row {
  display: grid;
  grid-template-columns: 1fr 108px;
  gap: 10px;
}
.captcha {
  height: 46px;
  border: none;
  border-radius: 13px;
  background: linear-gradient(135deg,#e9f2ff,#dbe9ff);
  color: #315fc9;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 4px;
  cursor: pointer;
}
.error-text {
  margin: -3px 0 13px;
  font-size: 12px;
  color: #ef4444;
}
.primary-btn {
  width: 100%;
  height: 48px;
  margin-top: 4px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg,#4b7cff,#3670ff);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(54,112,255,.24);
}
.switch-text {
  margin-top: 20px;
  text-align: center;
  font-size: 13px;
  color: #64748b;
}
.switch-text a {
  color: #3670ff;
  text-decoration: none;
  font-weight: 600;
}
.back-home {
  display: block;
  margin-top: 14px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  text-decoration: none;
}
.primary-btn:disabled {
  opacity: .65;
  cursor: not-allowed;
}
</style>