<template>
  <div class="auth-page">
    <div class="auth-shell">
      <div class="brand">
        <div class="brand-icon">🌦️</div>
        <h1>创建账号</h1>
        <p>注册后可保存你的天气偏好与默认站点</p>
      </div>
      <div class="auth-card">
        <form @submit.prevent="handleRegister">
          <div class="form-item">
            <label>用户名</label>
            <input v-model.trim="form.username" type="text" placeholder="3～20个字符">
          </div>
          <div class="form-item">
            <label>昵称</label>
            <input v-model.trim="form.nickname" type="text" placeholder="例如：泉城天气观察员">
          </div>
          <div class="form-item">
            <label>手机号</label>
            <input v-model.trim="form.phone" type="text" maxlength="11" placeholder="请输入手机号">
          </div>
          <div class="form-item">
            <label>密码</label>
            <input v-model="form.password" type="password" placeholder="至少6位">
          </div>
          <div class="form-item">
            <label>确认密码</label>
            <input v-model="form.confirmPassword" type="password" placeholder="再次输入密码">
          </div>
          <div class="form-item">
            <label>验证码</label>
            <div class="captcha-row">
              <input v-model.trim="form.captcha" type="text" maxlength="4" placeholder="输入验证码">
              <button type="button" class="captcha" @click="refreshCaptcha">{{ captcha }}</button>
            </div>
          </div>
          <div class="agreement">
            <input id="agree" v-model="form.agree" type="checkbox">
            <label for="agree">我已阅读并同意用户服务协议与隐私说明</label>
          </div>
          <div v-if="errorText" class="error-text">{{ errorText }}</div>
          <div v-if="successText" class="success-text">{{ successText }}</div>

          <button
          class="primary-btn"
          type="submit"
          :disabled="submitting"
          >
          {{ submitting ? '正在注册...' : '注册账号' }}
          </button>
        </form>
        <div class="switch-text">
          已有账号？
          <router-link to="/login">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { registerUser } from '../api/auth'

const router = useRouter()
const captcha = ref('')
const errorText = ref('')
const successText = ref('')
const submitting = ref(false)

const form = reactive({
  username: '',
  nickname: '',
  phone: '',
  password: '',
  confirmPassword: '',
  captcha: '',
  agree: false
})

function refreshCaptcha() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let result = ''
  for (let i = 0; i < 4; i++) {
    result += chars[Math.floor(Math.random() * chars.length)]
  }
  captcha.value = result
}

async function handleRegister() {
  errorText.value = ''
  successText.value = ''

  if (form.username.length < 3 || form.username.length > 20) {
    errorText.value = '用户名长度应为3～20个字符'
    return
  }

  if (!form.nickname) {
    errorText.value = '请输入昵称'
    return
  }

  if (!/^1\d{10}$/.test(form.phone)) {
    errorText.value = '请输入正确的11位手机号'
    return
  }

  if (form.password.length < 6) {
    errorText.value = '密码至少6位'
    return
  }

  if (form.password !== form.confirmPassword) {
    errorText.value = '两次输入的密码不一致'
    return
  }

  if (form.captcha.toUpperCase() !== captcha.value) {
    errorText.value = '验证码错误'
    form.captcha = ''
    refreshCaptcha()
    return
  }

  if (!form.agree) {
    errorText.value = '请先同意用户服务协议与隐私说明'
    return
  }

  submitting.value = true

  try {
    const response = await registerUser({
      username: form.username,
      nickname: form.nickname,
      phone: form.phone,
      password: form.password
    })

    successText.value =
      response.data.message || '注册成功'

    setTimeout(() => {
      router.push('/login')
    }, 1000)

  } catch (err) {
    console.error('注册失败：', err)

    if (err.response?.data?.detail) {
      errorText.value = err.response.data.detail
    } else {
      errorText.value = '注册失败，请稍后重试'
    }

    refreshCaptcha()
    form.captcha = ''
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
  padding: 26px 16px 40px;
  background: linear-gradient(180deg,#dcecff 0%,#eef5ff 38%,#f7f9fc 100%);
}
.auth-shell {
  width: 100%;
  max-width: 430px;
}
.brand {
  padding: 15px 8px 23px;
  text-align: center;
}
.brand-icon {
  margin-bottom: 5px;
  font-size: 40px;
}
.brand h1 {
  margin: 0;
  font-size: 27px;
  color: #1e293b;
}
.brand p {
  margin: 7px 0 0;
  font-size: 12px;
  color: #64748b;
}
.auth-card {
  padding: 24px 22px;
  border-radius: 26px;
  background: rgba(255,255,255,.96);
  box-shadow: 0 14px 40px rgba(51,65,85,.12);
}
.form-item {
  margin-bottom: 14px;
}
.form-item label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}
.form-item input {
  width: 100%;
  height: 44px;
  box-sizing: border-box;
  padding: 0 13px;
  border: 1px solid #dbe4ef;
  border-radius: 13px;
  outline: none;
  background: #f8fafc;
  font-size: 14px;
}
.form-item input:focus {
  border-color: #4b7cff;
  background: white;
  box-shadow: 0 0 0 3px rgba(75,124,255,.08);
}
.captcha-row {
  display: grid;
  grid-template-columns: 1fr 108px;
  gap: 10px;
}
.captcha {
  height: 44px;
  border: none;
  border-radius: 13px;
  background: linear-gradient(135deg,#e9f2ff,#dbe9ff);
  color: #315fc9;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 4px;
  cursor: pointer;
}
.agreement {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 5px 0 15px;
  font-size: 11px;
  line-height: 1.5;
  color: #64748b;
}
.agreement input {
  margin-top: 2px;
}
.error-text {
  margin-bottom: 12px;
  font-size: 12px;
  color: #ef4444;
}
.primary-btn {
  width: 100%;
  height: 48px;
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
  margin-top: 19px;
  text-align: center;
  font-size: 13px;
  color: #64748b;
}
.switch-text a {
  color: #3670ff;
  text-decoration: none;
  font-weight: 600;
}

.success-text {
  margin-bottom: 12px;
  font-size: 12px;
  color: #22c55e;
}

.primary-btn:disabled {
  opacity: .65;
  cursor: not-allowed;
}
</style>