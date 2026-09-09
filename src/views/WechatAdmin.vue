<template>
  <div class="admin-page">
    <div class="admin-header">
      <div>
        <div class="admin-title">
          拾风观象台 · 内容管理
        </div>

        <div class="admin-subtitle">
          更新首页展示的最新公众号文章
        </div>
      </div>
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

      <div class="form-group">
        <label class="form-label">
          管理员密码
        </label>

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

      <button
        class="update-button"
        :disabled="loading"
        @click="updateArticle"
      >
        {{ loading ? '正在更新...' : '更新首页文章' }}
      </button>

      <div
        v-if="message"
        :class="[
          'result-message',
          success ? 'success' : 'error'
        ]"
      >
        {{ message }}
      </div>

    </div>

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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const articleUrl = ref('')
const password = ref('')
const showPassword = ref(false)

const loading = ref(false)
const message = ref('')
const success = ref(false)

const latestArticle = ref(null)

const BASE_URL = '/api'

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

async function updateArticle() {
  message.value = ''
  success.value = false

  const url = articleUrl.value.trim()
  const adminPassword = password.value.trim()

  if (!url) {
    message.value = '请先填写微信文章链接'
    return
  }

  if (!adminPassword) {
    message.value = '请输入管理员密码'
    return
  }

  loading.value = true

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
      success.value = true
      message.value =
        `更新成功：${data.title || ''}`

      await loadLatestArticle()

      password.value = ''
    } else {
      message.value =
        data?.error || '更新失败'
    }
  } catch (err) {
    console.error(
      '更新公众号文章失败：',
      err
    )

    message.value =
      '请求失败，请检查后端是否正常运行'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLatestArticle()
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

.admin-card {
  padding: 20px;
  border-radius: 20px;
  background: white;
  box-shadow:
    0 8px 24px rgba(15, 23, 42, 0.07);
}

.form-group {
  position: relative;
  margin-bottom: 20px;
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
  margin-bottom: 10px;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
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
</style>