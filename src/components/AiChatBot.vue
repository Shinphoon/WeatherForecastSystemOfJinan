<template>
  <div class="ai-chat">
    <MessageCenter
      :alert-data="alertData"
      :loading="alertLoading"
      :open="notificationsOpened"
      @update:open="notificationsOpened = $event; opened = false"
    />
    <!-- 聊天窗口 -->
    <div
      v-if="opened"
      class="ai-panel"
    >
      <div class="ai-header">
        <div>
          <div class="ai-title">
            🤖 济南天气 AI
          </div>
          <div class="ai-subtitle">
            DeepSeek 驱动
          </div>
        </div>

        <button
          class="close-btn"
          @click="opened = false"
        >
          ×
        </button>
      </div>

      <div
        ref="messageBox"
        class="message-list"
      >
        <div
          v-for="(item, index) in messages"
          :key="index"
          class="message-row"
          :class="item.role"
        >
          <div
            class="message-bubble"
            v-html="renderMarkdown(item.content)"
          ></div>
        </div>

        <div
          v-if="loading"
          class="message-row assistant"
        >
          <div class="message-bubble typing">
            正在思考...
          </div>
        </div>
      </div>

      <div class="ai-input-area">
        <textarea
          v-model="input"
          rows="1"
          placeholder="问问天气、雷达、出行..."
          @keydown.enter.exact.prevent="sendMessage"
        />

        <button
          class="send-btn"
          :disabled="loading || !input.trim()"
          @click="sendMessage"
        >
          发送
        </button>
      </div>
    </div>

    <!-- 悬浮机器人 -->
    <button
      class="ai-float-btn"
      aria-label="天气 AI 助手"
      @click="opened = !opened; notificationsOpened = false"
    >
      🤖
    </button>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import MessageCenter from './MessageCenter.vue'

const opened = ref(false)
const notificationsOpened = ref(false)

const input = ref('')

const loading = ref(false)

const messageBox = ref(null)

const messages = ref([
  {
    role: 'assistant',
    content:
      '你好，我是济南天气 AI 助手。你可以问我天气、雷达、预报或出行问题。'
  }
])
const props = defineProps({
  alertData: { type: Object, default: () => ({}) },
  alertLoading: { type: Boolean, default: false },
  stationId: {
    type: String,
    default: null
  },

  userLocation: {
    type: Object,
    default: () => ({
      lat: null,
      lng: null
    })
  }
})

async function scrollToBottom() {
  await nextTick()

  if (messageBox.value) {
    messageBox.value.scrollTop =
      messageBox.value.scrollHeight
  }
}

marked.setOptions({
  breaks: true,
  gfm: true
})

function renderMarkdown(text) {
  if (!text) {
    return ''
  }

  return DOMPurify.sanitize(
    marked.parse(text)
  )
}

async function sendMessage() {
  const text =
    input.value.trim()

  if (!text || loading.value) {
    return
  }

  const history =
    messages.value.map(item => ({
      role: item.role,
      content: item.content
    }))

  // 用户消息
  messages.value.push({
    role: 'user',
    content: text
  })

  input.value = ''

  // 先创建一个空的AI消息
  messages.value.push({
    role: 'assistant',
    content: ''
  })

  const assistantIndex =
    messages.value.length - 1

  loading.value = true

  await scrollToBottom()

  try {
    const response = await fetch(
      '/api/ai/chat',
      {
        method: 'POST',

        headers: {
          'Content-Type':
            'application/json'
        },

        body: JSON.stringify({
          message: text,

          history,

          station_id:
            props.stationId,

          lat:
            props.userLocation?.lat,

          lng:
            props.userLocation?.lng
        })
      }
    )

    if (!response.ok) {
      const errorText =
        await response.text()

      throw new Error(
        errorText ||
        'AI请求失败'
      )
    }

    if (!response.body) {
      throw new Error(
        '浏览器不支持流式响应'
      )
    }

    const reader =
      response.body.getReader()

    const decoder =
      new TextDecoder('utf-8')

    while (true) {
      const {
        done,
        value
      } = await reader.read()

      if (done) {
        break
      }

      const chunk =
        decoder.decode(
          value,
          {
            stream: true
          }
        )

      messages.value[
        assistantIndex
      ].content += chunk

      await scrollToBottom()
    }

  } catch (error) {
    console.error(
      'AI聊天失败：',
      error
    )

    messages.value[
      assistantIndex
    ].content =
      '抱歉，AI助手暂时无法连接，请稍后再试。'

  } finally {
    loading.value = false

    await scrollToBottom()
  }
}
</script>

<style scoped>
.ai-chat {
  position: relative;
  z-index: 9999;
}

.ai-float-btn {
  position: fixed;
  right: 22px;
  bottom: 92px;

  width: 56px;
  height: 56px;

  border: none;
  border-radius: 50%;

  background: linear-gradient(
    135deg,
    #4f7cff,
    #6d5dfc
  );

  color: white;
  font-size: 27px;

  box-shadow:
    0 8px 24px
    rgba(79, 124, 255, .35);

  cursor: pointer;

  z-index: 10001;
}

.ai-panel {
  position: fixed;

  right: 18px;
  bottom: 158px;

  width: min(
    360px,
    calc(100vw - 36px)
  );

  height: 520px;
  max-height:
    calc(100vh - 210px);

  display: flex;
  flex-direction: column;

  background: white;

  border-radius: 22px;

  overflow: hidden;

  box-shadow:
    0 12px 40px
    rgba(15, 23, 42, .18);

  z-index: 10000;
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 15px 17px;

  background: linear-gradient(
    135deg,
    #edf4ff,
    #f4f1ff
  );
}

.ai-title {
  font-size: 16px;
  font-weight: 700;
  color: #172554;
}

.ai-subtitle {
  margin-top: 2px;

  font-size: 11px;
  color: #94a3b8;
}

.close-btn {
  width: 32px;
  height: 32px;

  border: none;
  border-radius: 50%;

  background:
    rgba(255, 255, 255, .75);

  font-size: 22px;
  color: #64748b;

  cursor: pointer;
}

.message-list {
  flex: 1;

  overflow-y: auto;

  padding: 15px;

  background: #f8fafc;
}

.message-row {
  display: flex;
  margin-bottom: 11px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 82%;

  padding: 10px 13px;

  border-radius: 15px;

  font-size: 13px;
  line-height: 1.6;

  white-space: normal;
  word-break: break-word;
}

.assistant .message-bubble {
  background: white;

  color: #334155;

  border-bottom-left-radius: 5px;

  box-shadow:
    0 2px 8px
    rgba(15, 23, 42, .05);
}

.user .message-bubble {
  background: #4f7cff;
  color: white;

  border-bottom-right-radius: 5px;
}

.typing {
  color: #94a3b8;
}

.ai-input-area {
  display: flex;
  align-items: flex-end;

  gap: 8px;

  padding: 12px;

  border-top:
    1px solid #eef2f7;

  background: white;
}

.ai-input-area textarea {
  flex: 1;

  min-height: 40px;
  max-height: 90px;

  resize: none;

  padding: 10px 12px;

  border:
    1px solid #e2e8f0;

  border-radius: 13px;

  outline: none;

  font-size: 13px;
  font-family: inherit;
}

.ai-input-area textarea:focus {
  border-color: #4f7cff;
}

.send-btn {
  height: 40px;

  padding: 0 14px;

  border: none;
  border-radius: 12px;

  background: #4f7cff;

  color: white;

  font-size: 13px;
  font-weight: 600;

  cursor: pointer;
}

.send-btn:disabled {
  opacity: .45;
  cursor: default;
}

.message-bubble :deep(p) {
  margin: 0 0 6px;
}

.message-bubble :deep(p:last-child) {
  margin-bottom: 0;
}

.message-bubble :deep(strong) {
  font-weight: 700;
}

.message-bubble :deep(ul),
.message-bubble :deep(ol) {
  margin: 5px 0;
  padding-left: 22px;
}

.message-bubble :deep(li) {
  margin: 2px 0;
}

.message-bubble :deep(h1),
.message-bubble :deep(h2),
.message-bubble :deep(h3),
.message-bubble :deep(h4) {
  margin: 8px 0 5px;
  line-height: 1.4;
}

.message-bubble :deep(br) {
  line-height: 1.2;
}
</style>
