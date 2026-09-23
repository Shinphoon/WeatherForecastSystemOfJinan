<template>
  <section class="users-panel" @click.stop>
    <header><div><h2>用户管理</h2><p>共 {{ total }} 位用户 · 查看资料与管理账号状态</p></div><button :disabled="loading || saving !== null" @click="loadUsers">刷新</button></header>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-if="notice" class="notice" role="status">{{ notice }}</p>
    <p v-if="loading" class="empty">正在加载用户…</p>
    <p v-else-if="!users.length && !error" class="empty">暂无用户</p>
    <article v-for="user in users" :key="user.id" class="user-card">
      <button class="user-heading" :aria-expanded="expanded.has(user.id)" @click="toggleUser(user.id)">
        <strong>{{ user.nickname || user.username }} <small>#{{ user.id }}</small></strong>
        <span class="heading-right"><span :class="['status', { banned: user.status !== 1 }]">{{ user.status === 1 ? '正常' : '已封禁' }}</span><span class="chevron">{{ expanded.has(user.id) ? '⌃' : '⌄' }}</span></span>
      </button>
      <div v-if="expanded.has(user.id)" class="user-details">
      <dl>
        <dt>用户名</dt><dd>{{ user.username }}</dd>
        <dt>角色</dt><dd>{{ user.role === 'admin' ? '管理员' : '普通用户' }}</dd>
        <dt>手机号</dt><dd>{{ user.phone || '未绑定' }}</dd>
        <dt>邮箱</dt><dd>{{ user.email || '未绑定' }}</dd>
        <dt>推送</dt><dd>{{ user.push_enable ? '已开启' : '已关闭' }}</dd>
        <dt>所在地</dt><dd>{{ user.last_address || '未设置' }}</dd>
        <dt>经纬度</dt><dd>{{ user.last_lng ?? '—' }} / {{ user.last_lat ?? '—' }}</dd>
        <dt>注册时间</dt><dd>{{ formatTime(user.create_time) }}</dd>
        <dt>更新时间</dt><dd>{{ formatTime(user.update_time) }}</dd>
      </dl>
      <div class="saved-places">
        <strong>首页保存地点（{{ user.saved_locations?.length || 0 }}/5）</strong>
        <p v-if="!user.saved_locations?.length">暂无保存地点</p>
        <ul v-else><li v-for="place in user.saved_locations" :key="place.id"><b>{{ place.name }}</b><span>{{ place.address }}</span><small>{{ place.lng }}, {{ place.lat }}<template v-if="place.station_name"> · 最近国家站：{{ place.station_name }} {{ place.station_id }}</template></small></li></ul>
      </div>
      <div v-if="user.role !== 'admin' && user.id !== viewerId" class="user-actions">
        <template v-if="confirmId === user.id">
          <p>{{ user.status === 1 ? '封禁后，该用户将无法登录，已有登录凭证也将被拒绝。' : '解封后，该用户可以重新登录。' }}</p>
          <button :disabled="saving !== null" @click="changeStatus(user)">{{ saving === user.id ? '正在保存…' : '确认' + (user.status === 1 ? '封禁' : '解封') }}</button>
          <button :disabled="saving !== null" @click="confirmId = null">取消</button>
        </template>
        <button v-else :class="{ danger: user.status === 1 }" :disabled="saving !== null" @click="confirmId = user.id">{{ user.status === 1 ? '封禁账号' : '解封账号' }}</button>
      </div>
      <p v-else class="protected">管理员账号不支持在此封禁</p>
      </div>
    </article>
    <footer v-if="total > pageSize"><button :disabled="page <= 1 || loading || saving !== null" @click="page--; loadUsers()">上一页</button><span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span><button :disabled="page * pageSize >= total || loading || saving !== null" @click="page++; loadUsers()">下一页</button></footer>
  </section>
</template>

<script setup>
import { ref, onActivated, onDeactivated, onBeforeUnmount } from 'vue'
import axios from 'axios'
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const saving = ref(null)
const error = ref('')
const notice = ref('')
const confirmId = ref(null)
const viewerId = ref(null)
const expanded = ref(new Set())
let revision = 0
const headers = () => ({ Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` })
const formatTime = value => value ? value.replace('T', ' ').slice(0, 19) : '—'
function toggleUser(id) { expanded.value.has(id) ? expanded.value.delete(id) : expanded.value.add(id) }
async function loadUsers() {
  const request = ++revision
  loading.value = true
  error.value = ''
  users.value = []
  expanded.value.clear()
  confirmId.value = null
  try {
    const { data } = await axios.get('/api/admin/users', { headers: headers(), params: { page: page.value, page_size: pageSize } })
    if (request !== revision) return
    users.value = data.users
    total.value = data.total
    viewerId.value = data.viewer_id
  } catch (err) {
    if (request === revision) {
      total.value = 0
      error.value = err.response?.data?.detail || '用户数据读取失败，请稍后重试'
    }
  } finally { if (request === revision) loading.value = false }
}
async function changeStatus(user) {
  saving.value = user.id
  error.value = notice.value = ''
  const request = revision
  try {
    const { data } = await axios.put(`/api/admin/users/${user.id}/status`, { status: user.status === 1 ? 0 : 1 }, { headers: headers() })
    if (request !== revision) return
    user.status = data.status
    notice.value = data.message
    confirmId.value = null
  } catch (err) {
    if (request === revision) error.value = err.response?.data?.detail || '状态修改失败，请重试'
  } finally { saving.value = null }
}
onActivated(() => { page.value = 1; notice.value = ''; loadUsers() })
function clear() { revision++; users.value = []; total.value = 0; confirmId.value = null; expanded.value.clear() }
onDeactivated(clear)
onBeforeUnmount(clear)
</script>

<style scoped>
.users-panel { background: white; padding: 20px; border-radius: 20px; margin-bottom: 24px; color: #334155; box-shadow: 0 6px 24px #182f5210; }
header, footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
h2 { margin: 0; font-size: 19px; }
header p, .protected { font-size: 12px; color: #94a3b8; }
button { border: 0; background: #edf4ff; color: #3977e7; padding: 9px 13px; border-radius: 9px; cursor: pointer; white-space: nowrap; }
button:disabled { opacity: .5; cursor: default; }
button:focus-visible { outline: 2px solid #3977e7; outline-offset: 2px; }
.user-card { background: #f8faff; border: 1px solid #e8edf5; border-radius: 14px; padding: 0; margin-top: 12px; overflow:hidden; }
.user-heading { display:flex; width:100%; justify-content:space-between; align-items:center; gap:12px; padding:14px; border:0; border-radius:0; background:transparent; color:#334155; text-align:left; }
.heading-right { display:flex; align-items:center; gap:10px; }.chevron{width:24px;color:#3977e7;font-size:19px;text-align:center}.user-details{padding:0 14px 14px;border-top:1px solid #e8edf5}
.user-heading strong { overflow-wrap: anywhere; min-width: 0; }
small { color: #94a3b8; font-weight: normal; }
.status { background: #e5f7ef; color: #23825b; border-radius: 6px; padding: 3px 7px; font-size: 12px; white-space: nowrap; }
.status.banned, button.danger { background: #fff0f0; color: #d94949; }
dl { display: grid; grid-template-columns: 65px minmax(0, 1fr); gap: 7px 10px; font-size: 12px; }
dt { color: #8996aa; } dd { margin: 0; overflow-wrap: anywhere; }
.saved-places{margin:14px 0;padding:12px;border-radius:10px;background:white;font-size:12px}.saved-places>strong{color:#475569}.saved-places p{margin-bottom:0;color:#94a3b8}.saved-places ul{list-style:none;margin:8px 0 0;padding:0}.saved-places li{padding:8px 0;border-top:1px solid #edf1f6}.saved-places li b,.saved-places li span,.saved-places li small{display:block;overflow-wrap:anywhere}.saved-places li span{margin-top:3px;color:#64748b}.saved-places li small{margin-top:3px}
.user-actions { text-align: right; } .user-actions p { text-align: left; color: #64748b; font-size: 12px; }
.user-actions button + button { margin-left: 8px; }
.error { color: #d94949; font-size: 13px; } .notice { color: #23825b; font-size: 13px; }
.empty { padding: 22px 0; text-align: center; color: #94a3b8; font-size: 13px; }
footer { margin-top: 18px; font-size: 12px; }
</style>
