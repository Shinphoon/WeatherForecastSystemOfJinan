import { ref } from 'vue'
import axios from 'axios'

export const dailyMessages = ref([])
export const notificationError = ref('')
let activeToken = null
let lastAttempt = 0
let pending = null

export async function syncDailyBriefing(force = false) {
  const token = localStorage.getItem('access_token')
  if (token !== activeToken) {
    activeToken = token
    dailyMessages.value = []
    notificationError.value = ''
    lastAttempt = 0
    pending = null
  }
  if (!token) return
  if (pending) return pending
  if (!force && Date.now() - lastAttempt < 60000) return
  lastAttempt = Date.now()
  const request = (async () => {
    try {
      const response = await axios.post('/api/auth/daily-briefing', {}, {
        headers: { Authorization: `Bearer ${token}` }, timeout: 60000
      })
      if (activeToken === token) {
        dailyMessages.value = response.data.messages
        notificationError.value = ''
      }
    } catch (error) {
      if (activeToken === token) {
        if (error.response?.status === 401) dailyMessages.value = []
        notificationError.value = error.response?.status === 401 ? '请重新登录后查看每日早报。' : '早报暂时无法加载，稍后将自动重试。'
      }
    } finally { if (pending === request) pending = null }
  })()
  pending = request
  return request
}

export async function markDailyRead(ids) {
  const token = localStorage.getItem('access_token')
  if (!token || !ids.length) return
  const response = await axios.put('/api/auth/notifications/read', { ids }, {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (activeToken === token) dailyMessages.value = response.data.messages
}
