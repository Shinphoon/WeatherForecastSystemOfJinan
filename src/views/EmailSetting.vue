<template>
  <div class="email-page">
    <header class="page-header">
      <button
        class="back-btn"
        @click="router.back()"
      >
        ‹
      </button>

      <div>
        <h1>邮箱设置</h1>
        <p>支持 Gmail / QQ / 126 / 163 等邮箱，接收天气预警与早午晚天气报告</p>
      </div>
    </header>

    <section class="email-card">
      <label class="label">
        邮箱地址
      </label>

      <input
        v-model="email"
        type="email"
        class="email-input"
        placeholder="例如 example@qq.com"
      >

      <div
        v-if="message"
        :class="[
          'message',
          success ? 'success' : 'error'
        ]"
      >
        {{ message }}
      </div>

      <button
        class="save-btn"
        :disabled="saving"
        @click="saveEmail"
      >
        {{ saving ? '正在保存...' : '保存邮箱' }}
      </button>

      <button
        v-if="currentEmail"
        class="delete-btn"
        :disabled="saving"
        @click="deleteEmail"
      >
        删除邮箱
      </button>
    </section>
    <ReportSchedule />
  </div>
</template>

<script setup>
import ReportSchedule from '../components/ReportSchedule.vue'
import {
  ref,
  onMounted
} from 'vue'

import {
  useRouter
} from 'vue-router'

import {
  getCurrentUser,
  updateEmail
} from '../api/auth'

const router = useRouter()

const email = ref('')
const currentEmail = ref('')

const saving = ref(false)
const message = ref('')
const success = ref(false)

async function loadEmail() {
  try {
    const response =
      await getCurrentUser()

    currentEmail.value =
      response.data.email || ''

    email.value =
      currentEmail.value

  } catch (err) {
    console.error(
      '获取邮箱失败：',
      err
    )
  }
}

async function saveEmail() {
  message.value = ''

  const value =
    email.value.trim()

  if (!value) {
    success.value = false
    message.value = '请输入邮箱'
    return
  }

  if (
    !value.includes('@') ||
    !value.includes('.')
  ) {
    success.value = false
    message.value = '邮箱格式不正确'
    return
  }

  saving.value = true

  try {
    const response =
      await updateEmail(value)

    currentEmail.value =
      response.data.email || ''

    email.value =
      currentEmail.value

    success.value = true

    message.value =
      response.data.message ||
      '邮箱保存成功'

  } catch (err) {
    success.value = false

    message.value =
      err.response?.data?.detail ||
      '邮箱保存失败'

  } finally {
    saving.value = false
  }
}

async function deleteEmail() {
  const confirmed =
    window.confirm(
      '确定删除当前邮箱吗？删除后将无法接收邮件预警。'
    )

  if (!confirmed) {
    return
  }

  saving.value = true
  message.value = ''

  try {
    const response =
      await updateEmail(null)

    currentEmail.value = ''
    email.value = ''

    success.value = true

    message.value =
      response.data.message ||
      '邮箱已删除'

  } catch (err) {
    success.value = false

    message.value =
      err.response?.data?.detail ||
      '邮箱删除失败'

  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadEmail()
})
</script>

<style scoped>
.email-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 20px 16px;
  background: linear-gradient(
    180deg,
    #eaf4ff 0%,
    #f5f8fc 280px,
    #f5f7fa 100%
  );
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 26px;
  color: #1e293b;
}

.page-header p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #94a3b8;
}

.back-btn {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 50%;
  background: white;
  font-size: 28px;
  cursor: pointer;
}

.email-card {
  padding: 20px;
  border-radius: 22px;
  background: white;
  box-shadow: 0 8px 24px rgba(0,0,0,.06);
}

.label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #475569;
}

.email-input {
  width: 100%;
  box-sizing: border-box;
  height: 48px;
  padding: 0 14px;
  border: 1px solid #dbe4ef;
  border-radius: 14px;
  outline: none;
  font-size: 15px;
}

.message {
  margin-top: 12px;
  font-size: 13px;
}

.success {
  color: #16a34a;
}

.error {
  color: #ef4444;
}

.save-btn,
.delete-btn {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.save-btn {
  margin-top: 18px;
  background: linear-gradient(
    135deg,
    #4b7cff,
    #3670ff
  );
  color: white;
}

.delete-btn {
  margin-top: 12px;
  background: #fff1f2;
  color: #e11d48;
}

button:disabled {
  opacity: .6;
  cursor: not-allowed;
}
</style>
