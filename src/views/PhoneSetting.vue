<template>
  <div class="phone-page">
    <header class="page-header">
      <button class="back-btn" @click="router.back()">‹</button>

      <div>
        <h1>修改手机号</h1>
        <p>更新账号绑定的手机号码</p>
      </div>
    </header>

    <section class="phone-card">
      <div class="form-item">
        <label>新手机号</label>

        <input
          v-model.trim="phone"
          type="tel"
          maxlength="11"
          placeholder="请输入11位手机号"
        >
      </div>

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
        class="submit-btn"
        :disabled="submitting"
        @click="changePhone"
      >
        {{ submitting ? '正在保存...' : '保存手机号' }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { updatePhone } from '../api/auth'

const router = useRouter()

const phone = ref('')
const submitting = ref(false)
const message = ref('')
const success = ref(false)

async function changePhone() {
  message.value = ''
  success.value = false

  if (
    phone.value.length !== 11 ||
    !/^\d{11}$/.test(phone.value)
  ) {
    message.value = '请输入正确的11位手机号'
    return
  }

  submitting.value = true

  try {
    const response =
      await updatePhone(phone.value)

    success.value = true
    message.value =
      response.data.message || '手机号修改成功'

  } catch (err) {
    success.value = false

    message.value =
      err.response?.data?.detail ||
      '手机号修改失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.phone-page {
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
  color: #334155;
  cursor: pointer;
}

.phone-card {
  padding: 20px;
  border-radius: 22px;
  background: white;
  box-shadow:
    0 8px 24px rgba(0,0,0,.06);
}

.form-item {
  margin-bottom: 18px;
}

.form-item label {
  display: block;
  margin-bottom: 7px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
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
}

.form-item input:focus {
  border-color: #4b7cff;
  background: white;
}

.message {
  margin-bottom: 14px;
  font-size: 13px;
}

.message.success {
  color: #16a34a;
}

.message.error {
  color: #ef4444;
}

.submit-btn {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(
    135deg,
    #4b7cff,
    #3670ff
  );
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.submit-btn:disabled {
  opacity: .6;
  cursor: not-allowed;
}
</style>