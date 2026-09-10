<template>
  <div class="location-page">
    <header class="page-header">
      <button class="back-btn" @click="router.back()">‹</button>
      <div>
        <h1>最近位置</h1>
        <p>获取并保存当前所在位置</p>
      </div>
    </header>

    <section class="location-card">
      <div class="location-info">
        <div>经度：{{ longitude ?? '--' }}</div>
        <div>纬度：{{ latitude ?? '--' }}</div>
      </div>

      <div
        v-if="message"
        :class="['message', success ? 'success' : 'error']"
      >
        {{ message }}
      </div>

      <button
        class="locate-btn"
        :disabled="locating"
        @click="getLocation"
      >
        {{ locating ? '正在定位...' : '获取当前位置' }}
      </button>

      <button
        class="save-btn"
        :disabled="!longitude || !latitude || saving"
        @click="saveLocation"
      >
        {{ saving ? '正在保存...' : '保存当前位置' }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { updateLocation } from '../api/auth'

const router = useRouter()

const longitude = ref(null)
const latitude = ref(null)

const locating = ref(false)
const saving = ref(false)

const message = ref('')
const success = ref(false)

function getLocation() {
  message.value = ''
  success.value = false

  if (!navigator.geolocation) {
    message.value = '当前浏览器不支持定位'
    return
  }

  locating.value = true

  navigator.geolocation.getCurrentPosition(
    (position) => {
      longitude.value =
        Number(position.coords.longitude.toFixed(6))

      latitude.value =
        Number(position.coords.latitude.toFixed(6))

      success.value = true
      message.value = '定位成功'
      locating.value = false
    },

    (error) => {
      console.error(error)

      success.value = false
      message.value = '定位失败，请检查浏览器定位权限'
      locating.value = false
    },

    {
      enableHighAccuracy: true,
      timeout: 10000
    }
  )
}

async function saveLocation() {
  saving.value = true
  message.value = ''

  try {
    const response = await updateLocation(
      longitude.value,
      latitude.value
    )

    success.value = true
    message.value =
      response.data.message || '位置保存成功'

  } catch (err) {
    success.value = false
    message.value =
      err.response?.data?.detail || '位置保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.location-page {
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

.location-card {
  padding: 20px;
  border-radius: 22px;
  background: white;
  box-shadow: 0 8px 24px rgba(0,0,0,.06);
}

.location-info {
  line-height: 2;
  margin-bottom: 16px;
  color: #334155;
}

.message {
  margin-bottom: 14px;
  font-size: 13px;
}

.success {
  color: #16a34a;
}

.error {
  color: #ef4444;
}

.locate-btn,
.save-btn {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.locate-btn {
  margin-bottom: 12px;
  background: #eef4ff;
  color: #3670ff;
}

.save-btn {
  background: linear-gradient(
    135deg,
    #4b7cff,
    #3670ff
  );
  color: white;
}

button:disabled {
  opacity: .6;
  cursor: not-allowed;
}
</style>