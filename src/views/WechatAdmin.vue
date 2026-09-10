<template>
  <div class="admin-page">
    <div class="admin-header">
      <div class="admin-title">拾风观象台 · 管理中心</div>
      <div class="admin-subtitle">
        管理首页公众号文章与国家气象站
      </div>
    </div>

    <!-- 管理员密码 -->
    <div class="admin-card password-card">
      <div class="section-heading">管理员验证</div>

      <div class="form-group no-bottom">
        <label class="form-label">管理员密码</label>

        <input
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          class="form-input"
          placeholder="请输入管理员密码"
        >

        <button
          type="button"
          class="password-toggle"
          @click="showPassword = !showPassword"
        >
          {{ showPassword ? '隐藏密码' : '显示密码' }}
        </button>
      </div>
    </div>

    <!-- 公众号文章管理 -->
    <div class="section-title">
      公众号文章
    </div>

    <div class="admin-card">
      <div class="form-group">
        <label class="form-label">
          微信文章链接
        </label>

        <textarea
          v-model="articleUrl"
          class="form-textarea"
          placeholder="请粘贴 https://mp.weixin.qq.com/... 文章链接"
        ></textarea>
      </div>

      <button
        class="update-button"
        :disabled="articleLoading"
        @click="updateArticle"
      >
        {{
          articleLoading
            ? '正在更新...'
            : '更新首页文章'
        }}
      </button>

      <div
        v-if="articleMessage"
        :class="[
          'result-message',
          articleSuccess ? 'success' : 'error'
        ]"
      >
        {{ articleMessage }}
      </div>
    </div>

    <!-- 当前公众号文章 -->
    <div
      v-if="latestArticle"
      class="preview-section"
    >
      <div class="preview-title">
        当前首页文章
      </div>

      <a
        :href="latestArticle.url"
        target="_blank"
        rel="noopener noreferrer"
        class="preview-card"
      >
        <img
          v-if="latestArticle.cover"
          :src="latestArticle.cover"
          class="preview-cover"
          referrerpolicy="no-referrer"
        >

        <div class="preview-content">
          <div class="preview-account">
            拾风观象台
          </div>

          <div class="preview-article-title">
            {{ latestArticle.title }}
          </div>

          <div class="preview-meta">
            <span>
              {{ latestArticle.author }}
            </span>

            <span>
              {{ latestArticle.publish_time }}
            </span>
          </div>
        </div>
      </a>
    </div>

    <!-- 添加国家气象站 -->
    <div class="section-title station-section-title">
      国家气象站
    </div>

    <div class="admin-card">
      <div class="section-heading">
        添加国家气象站
      </div>

      <div class="station-form-grid">
        <div class="form-group">
          <label class="form-label">
            国家站站号
          </label>

          <input
            v-model="stationId"
            class="form-input normal-input"
            maxlength="5"
            inputmode="numeric"
            placeholder="例如 54831"
          >
        </div>

        <div class="form-group">
          <label class="form-label">
            站点名称
          </label>

          <input
            v-model="stationName"
            class="form-input normal-input"
            placeholder="例如 潍坊"
          >
        </div>

        <div class="form-group">
          <label class="form-label">
            纬度
          </label>

          <input
            v-model="stationLat"
            type="number"
            step="0.0001"
            class="form-input normal-input"
            placeholder="例如 36.7069"
          >
        </div>

        <div class="form-group">
          <label class="form-label">
            经度
          </label>

          <input
            v-model="stationLon"
            type="number"
            step="0.0001"
            class="form-input normal-input"
            placeholder="例如 119.1618"
          >
        </div>
      </div>

      <button
        class="update-button"
        :disabled="stationLoading"
        @click="addStation"
      >
        {{
          stationLoading
            ? '正在添加...'
            : '添加国家站'
        }}
      </button>

      <div
        v-if="stationMessage"
        :class="[
          'result-message',
          stationSuccess ? 'success' : 'error'
        ]"
      >
        {{ stationMessage }}
      </div>
    </div>

    <!-- 当前站点列表 -->
    <div class="station-list-section">
      <div class="station-list-header">
        <div class="preview-title">
          当前国家站
        </div>

        <div class="station-count">
          {{ stations.length }} 个
        </div>
      </div>

      <div
        v-if="stationsLoading"
        class="station-empty"
      >
        正在读取站点...
      </div>

      <div
        v-else-if="stations.length === 0"
        class="station-empty"
      >
        暂无站点数据
      </div>

      <div
        v-else
        class="station-list"
      >
        <div
          v-for="station in stations"
          :key="station.station || station.id"
          class="station-item"
        >
          <div class="station-main">
            <div class="station-name">
              {{ station.name }}
            </div>

            <div class="station-id">
              {{ station.station || station.id }}
            </div>
          </div>

          <div class="station-location">
            <span>
              纬度 {{ formatCoordinate(station.lat) }}
            </span>

            <span>
              经度 {{ formatCoordinate(station.lon) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const BASE_URL = '/api'

const password = ref('')
const showPassword = ref(false)

const articleUrl = ref('')
const articleLoading = ref(false)
const articleMessage = ref('')
const articleSuccess = ref(false)
const latestArticle = ref(null)

const stationId = ref('')
const stationName = ref('')
const stationLat = ref('')
const stationLon = ref('')
const stationLoading = ref(false)
const stationMessage = ref('')
const stationSuccess = ref(false)

const stations = ref([])
const stationsLoading = ref(false)

async function loadLatestArticle() {
  try {
    const response = await axios.get(
      `${BASE_URL}/weather/wechat/latest`
    )

    if (
      response.data &&
      response.data.success
    ) {
      latestArticle.value =
        response.data

      articleUrl.value =
        response.data.url || ''
    }
  } catch (err) {
    console.error(
      '读取当前公众号文章失败：',
      err
    )
  }
}

async function loadStations() {
  stationsLoading.value = true

  try {
    const response = await axios.get(
      `${BASE_URL}/weather/stations`
    )

    stations.value =
      Array.isArray(response.data)
        ? response.data
        : []
  } catch (err) {
    console.error(
      '读取国家站列表失败：',
      err
    )

    stations.value = []
  } finally {
    stationsLoading.value = false
  }
}

async function updateArticle() {
  articleMessage.value = ''
  articleSuccess.value = false

  const url = articleUrl.value.trim()
  const adminPassword =
    password.value.trim()

  if (!url) {
    articleMessage.value =
      '请先填写微信文章链接'
    return
  }

  if (!adminPassword) {
    articleMessage.value =
      '请输入管理员密码'
    return
  }

  articleLoading.value = true

  try {
    const response = await axios.post(
      `${BASE_URL}/weather/wechat/update`,
      {
        url: url,
        password: adminPassword
      }
    )

    const data = response.data

    if (data && data.success) {
      articleSuccess.value = true
      articleMessage.value =
        `更新成功：${data.title || ''}`

      await loadLatestArticle()
    } else {
      articleMessage.value =
        data?.error || '更新失败'
    }
  } catch (err) {
    console.error(
      '更新公众号文章失败：',
      err
    )

    articleMessage.value =
      '请求失败，请检查后端是否正常运行'
  } finally {
    articleLoading.value = false
  }
}

async function addStation() {
  stationMessage.value = ''
  stationSuccess.value = false

  const id = stationId.value.trim()
  const name = stationName.value.trim()
  const adminPassword =
    password.value.trim()

  if (!adminPassword) {
    stationMessage.value =
      '请输入管理员密码'
    return
  }

  if (!id) {
    stationMessage.value =
      '请输入国家站站号'
    return
  }

  if (!/^\d{5}$/.test(id)) {
    stationMessage.value =
      '国家站站号必须是5位数字'
    return
  }

  if (!name) {
    stationMessage.value =
      '请输入站点名称'
    return
  }

  if (
    stationLat.value === '' ||
    stationLon.value === ''
  ) {
    stationMessage.value =
      '请输入站点经纬度'
    return
  }

  const lat = Number(stationLat.value)
  const lon = Number(stationLon.value)

  if (
    !Number.isFinite(lat) ||
    lat < -90 ||
    lat > 90
  ) {
    stationMessage.value =
      '纬度必须在 -90 到 90 之间'
    return
  }

  if (
    !Number.isFinite(lon) ||
    lon < -180 ||
    lon > 180
  ) {
    stationMessage.value =
      '经度必须在 -180 到 180 之间'
    return
  }

  stationLoading.value = true

  try {
    const response = await axios.post(
      `${BASE_URL}/weather/stations/add`,
      {
        station_id: id,
        name: name,
        lat: lat,
        lon: lon,
        password: adminPassword
      }
    )

    const data = response.data

    if (data && data.success) {
      stationSuccess.value = true
      stationMessage.value =
        `添加成功：${name}（${id}）`

      stationId.value = ''
      stationName.value = ''
      stationLat.value = ''
      stationLon.value = ''

      await loadStations()
    } else {
      stationMessage.value =
        data?.error || '添加失败'
    }
  } catch (err) {
    console.error(
      '添加国家站失败：',
      err
    )

    stationMessage.value =
      '请求失败，请检查后端是否正常运行'
  } finally {
    stationLoading.value = false
  }
}

function formatCoordinate(value) {
  const number = Number(value)

  if (!Number.isFinite(number)) {
    return '--'
  }

  return number.toFixed(4)
}

onMounted(() => {
  loadLatestArticle()
  loadStations()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  padding: 24px 18px 100px;
  background: #f3f7fd;
}

.admin-header {
  margin-bottom: 20px;
}

.admin-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.admin-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #94a3b8;
}

.section-title {
  margin: 26px 2px 10px;
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
}

.station-section-title {
  margin-top: 30px;
}

.section-heading {
  margin-bottom: 18px;
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}

.admin-card {
  padding: 20px;
  border-radius: 20px;
  background: white;
  box-shadow:
    0 8px 24px rgba(15, 23, 42, 0.07);
}

.password-card {
  margin-bottom: 4px;
}

.form-group {
  position: relative;
  margin-bottom: 20px;
}

.form-group.no-bottom {
  margin-bottom: 0;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.form-input,
.form-textarea {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
  background: #f8fbff;
  color: #1e293b;
  font-size: 14px;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.form-input {
  height: 48px;
  padding: 0 95px 0 14px;
}

.normal-input {
  padding-right: 14px;
}

.form-textarea {
  min-height: 100px;
  padding: 13px 14px;
  resize: vertical;
  line-height: 1.5;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #4f8cff;
  box-shadow:
    0 0 0 3px
    rgba(79, 140, 255, 0.12);
}

.password-toggle {
  position: absolute;
  right: 12px;
  bottom: 13px;
  border: none;
  background: transparent;
  color: #4f8cff;
  font-size: 12px;
  cursor: pointer;
}

.update-button {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 14px;
  background:
    linear-gradient(
      135deg,
      #3d7dff,
      #68a7ff
    );
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow:
    0 6px 16px
    rgba(61, 125, 255, 0.25);
}

.update-button:disabled {
  opacity: 0.6;
  cursor: default;
}

.result-message {
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.result-message.success {
  background: #edf9f2;
  color: #15803d;
}

.result-message.error {
  background: #fff1f2;
  color: #dc2626;
}

.preview-section {
  margin-top: 24px;
}

.preview-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.preview-section > .preview-title {
  margin-bottom: 10px;
}

.preview-card {
  display: block;
  overflow: hidden;
  border-radius: 18px;
  background: white;
  text-decoration: none;
  color: inherit;
  box-shadow:
    0 6px 18px
    rgba(15, 23, 42, 0.07);
}

.preview-cover {
  display: block;
  width: 100%;
  height: 150px;
  object-fit: cover;
}

.preview-content {
  padding: 14px;
}

.preview-account {
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #4f8cff;
}

.preview-article-title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
  color: #1e293b;
}

.preview-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  font-size: 11px;
  color: #94a3b8;
}

.station-form-grid {
  display: grid;
  grid-template-columns:
    repeat(2, minmax(0, 1fr));
  gap: 0 12px;
}

.station-list-section {
  margin-top: 24px;
}

.station-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.station-count {
  padding: 4px 9px;
  border-radius: 999px;
  background: #eaf2ff;
  color: #3d7dff;
  font-size: 12px;
  font-weight: 600;
}

.station-list {
  overflow: hidden;
  border-radius: 18px;
  background: white;
  box-shadow:
    0 6px 18px
    rgba(15, 23, 42, 0.07);
}

.station-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 15px 16px;
  border-bottom: 1px solid #eef2f7;
}

.station-item:last-child {
  border-bottom: none;
}

.station-main {
  min-width: 76px;
}

.station-name {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.station-id {
  margin-top: 3px;
  font-size: 11px;
  color: #94a3b8;
}

.station-location {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  font-size: 11px;
  color: #64748b;
}

.station-empty {
  padding: 24px;
  border-radius: 18px;
  background: white;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

@media (max-width: 420px) {
  .station-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>