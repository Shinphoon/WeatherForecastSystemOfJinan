<template>
  <div class="message-center" @click.stop @keydown.esc.stop="close">
    <button ref="trigger" class="message-trigger" :aria-expanded="open" aria-controls="notification-panel"
      :aria-label="`消息中心，${unreadCount} 条未读`" title="消息中心" @click="emit('update:open', !open)">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z" stroke-linejoin="round" />
        <path d="M10 21h4" stroke-linecap="round" />
      </svg>
      <span v-if="unreadCount" class="unread-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <section v-if="open" id="notification-panel" class="notification-panel" role="region" aria-labelledby="notification-title">
      <header>
        <div><h2 id="notification-title">消息中心</h2><p aria-live="polite">{{ unreadCount ? `${unreadCount} 条未读消息` : '所有消息已读' }}</p></div>
        <button ref="closeButton" class="close-button" aria-label="关闭消息中心" @click="close">×</button>
      </header>
      <div class="message-toolbar">
        <span>天气通知 <span class="total-count">{{ messages.length }}</span></span>
        <button class="read-all" :disabled="!unreadCount" @click="markAllRead">✓ 一键已读</button>
      </div>
      <div class="notification-list">
        <div v-if="!messages.length" class="empty-state">
          <span aria-hidden="true">🔔</span>
          <strong>{{ loading ? '正在加载消息…' : '暂无消息' }}</strong>
          <p>{{ loading ? '请稍候' : '新的天气预警将在这里显示' }}</p>
        </div>
        <article v-for="message in messages" :key="message.id" class="notification" :class="{ unread: !isRead(message.id) }">
          <div class="notification-meta"><span>{{ message.kind || (message.mock ? '模拟预警' : '天气预警') }}</span><span>{{ isRead(message.id) ? '已读' : '未读' }}</span></div>
          <div class="notification-heading"><h3>{{ message.title }}</h3><button class="expand-message" :aria-expanded="expanded.has(message.id)" :aria-label="`${expanded.has(message.id) ? '收起' : '展开'}${message.title}详情`" @click="toggleDetails(message.id)">{{ expanded.has(message.id) ? '⌃' : '⌄' }}</button></div>
          <div v-if="expanded.has(message.id)">
          <p v-if="message.description" class="description">{{ message.description }}</p>
          <p v-if="message.sender" class="sender">{{ message.sender }}</p>
          <p v-if="message.email_status" class="sender">{{ message.email_error || emailStatus[message.email_status] }}</p>
          </div>
          <footer><time>{{ message.publish_time || '发布时间未知' }}</time><button v-if="!isRead(message.id)" @click="markRead(message.id)">标为已读</button></footer>
        </article>
      </div>
      <p v-if="storageError" class="storage-note" role="status">浏览器暂时无法保存，已读状态仅在本次访问有效。</p>
      <p v-if="notificationError || readError" class="storage-note" role="status">{{ readError || notificationError }}</p>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { dailyMessages, notificationError, syncDailyBriefing, markDailyRead } from '../api/notifications'

const readError = ref('')
const expanded = ref(new Set())
function toggleDetails(id) { if (expanded.value.has(id)) expanded.value.delete(id); else expanded.value.add(id) }
const emailStatus = { sent: '邮件服务器已接受投递，请留意收件箱或垃圾邮件', sending: '邮件发送中或待确认', pending: '邮件等待发送', no_email: '绑定 Gmail / QQ / 126 / 163 等邮箱后可接收邮件通知', disabled: '邮件推送已关闭', failed: '邮件未确认送达，请联系管理员检查邮件服务' }

const props = defineProps({
  alertData: { type: Object, default: () => ({}) },
  loading: Boolean,
  open: Boolean
})
const emit = defineEmits(['update:open'])
const storageKey = 'jinan-weather:read-notifications:v1'
const storageError = ref(false)
const trigger = ref(null)
const closeButton = ref(null)
let saved = []
try {
  const value = JSON.parse(localStorage.getItem(storageKey) || '[]')
  if (Array.isArray(value)) saved = value.filter(id => typeof id === 'string')
} catch { storageError.value = true }
const readIds = ref(new Set(saved))

const messages = computed(() => {
  const data = props.alertData
  const alerts = data.has_alert ? (data.alerts || (data.latest ? [data.latest] : [])) : []
  return [...dailyMessages.value, ...new Map(alerts.map(alert => {
    // Include the publication and content so revised warnings become unread again.
    const id = JSON.stringify([Boolean(data.mock), alert.title, alert.publish_time, alert.description])
    return [id, { ...alert, id, mock: Boolean(data.mock) }]
  })).values()]
})
const isRead = id => (id.startsWith('briefing:') || id.startsWith('rain:')) ? dailyMessages.value.find(item => item.id === id)?.read : readIds.value.has(id)
const unreadCount = computed(() => messages.value.filter(item => !isRead(item.id)).length)

function persist() {
  try {
    localStorage.setItem(storageKey, JSON.stringify([...readIds.value]))
    storageError.value = false
  } catch { storageError.value = true }
}
async function markRead(id) {
  if (!(id.startsWith('briefing:') || id.startsWith('rain:'))) { readIds.value.add(id); persist(); return }
  try { await markDailyRead([id]); readError.value = '' }
  catch { readError.value = '已读状态保存失败，请重试。' }
}
async function markAllRead() {
  const ids = dailyMessages.value.filter(item => !item.read).map(item => item.id)
  try { await markDailyRead(ids); readError.value = '' }
  catch { readError.value = '消息已读状态保存失败，请重试。' }
  messages.value.filter(item => !item.id.startsWith('briefing:') && !item.id.startsWith('rain:')).forEach(item => readIds.value.add(item.id))
  persist()
}
function close() { emit('update:open', false); trigger.value?.focus() }
watch(() => props.open, async open => {
  if (open) { syncDailyBriefing(true); await nextTick(); closeButton.value?.focus() }
})
</script>

<style scoped>
.notification-heading { display:flex; align-items:center; justify-content:space-between; gap:10px; }
.notification-heading h3 { min-width:0; }
.expand-message { flex-shrink:0; width:32px; height:32px; border:0; border-radius:9px; color:#5278ff; background:#e7efff; font-size:22px; }
.message-center { color: #25324a; font-family: inherit; }
button { font-family: inherit; cursor: pointer; }
button:focus-visible { outline: 3px solid #96b4ff; outline-offset: 3px; }
.message-trigger { position: fixed; right: 22px; bottom: 160px; width: 56px; height: 56px; border: 1px solid #e1eaff; border-radius: 50%; background: white; color: #5278ff; display: grid; place-items: center; box-shadow: 0 8px 24px #4f7cff26; z-index: 10001; }
.unread-badge { position: absolute; right: -3px; top: -3px; min-width: 19px; height: 19px; padding: 0 4px; box-sizing: border-box; border-radius: 12px; background: #f05c6c; color: white; border: 2px solid white; font-size: 10px; line-height: 15px; font-weight: 700; }
.notification-panel { position: fixed; right: 18px; bottom: 228px; width: min(360px, calc(100vw - 36px)); max-height: calc(100dvh - 246px); display: flex; flex-direction: column; overflow: hidden; background: white; border-radius: 22px; box-shadow: 0 12px 40px #0f172e2e; z-index: 10002; }
header { display: flex; justify-content: space-between; align-items: center; padding: 18px; background: linear-gradient(135deg, #edf4ff, #f4f1ff); }
h2 { margin: 0; font-size: 18px; color: #172554; }
header p { margin: 5px 0 0; font-size: 12px; color: #71809a; }
.close-button { width: 32px; height: 32px; border: 0; border-radius: 50%; background: #ffffffbb; color: #64748b; font-size: 24px; }
.message-toolbar { padding: 12px 18px; display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 13px; border-bottom: 1px solid #eef2f8; }
.total-count { color: #94a3b8; margin-left: 4px; }
.read-all, footer button { border: 0; background: transparent; color: #5278ff; padding: 6px 0; font-size: 12px; }
.read-all:disabled { color: #94a3b8; cursor: default; }
.notification-list { overflow-y: auto; overscroll-behavior: contain; padding: 12px; background: #f7f9fd; min-height: 0; }
.notification { padding: 14px; border: 1px solid #e8edf5; border-radius: 14px; background: white; margin-bottom: 10px; }
.notification:last-child { margin-bottom: 0; }
.notification.unread { border-color: #d9e4ff; background: #f0f5ff; }
.notification-meta { display: flex; justify-content: space-between; color: #8995aa; font-size: 11px; }
.unread .notification-meta { color: #5278ff; }
h3 { margin: 9px 0; font-size: 14px; line-height: 1.6; overflow-wrap: anywhere; }
.description { font-size: 13px; line-height: 1.75; color: #5e6d83; white-space: pre-wrap; overflow-wrap: anywhere; margin: 0; }
.sender { color: #8995aa; font-size: 11px; margin: 10px 0 0; }
footer { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; margin-top: 8px; }
time { color: #8995aa; font-size: 11px; }
.empty-state { padding: 30px 10px; text-align: center; color: #8995aa; }
.empty-state > span { display: block; font-size: 32px; margin-bottom: 14px; }
.empty-state strong { color: #5e6d83; font-size: 14px; }
.empty-state p, .storage-note { font-size: 12px; }
.storage-note { margin: 0; padding: 8px 14px; color: #97713b; }
@media (max-height: 520px) { .notification-panel { bottom: 85px; max-height: calc(100dvh - 100px); } }
</style>
