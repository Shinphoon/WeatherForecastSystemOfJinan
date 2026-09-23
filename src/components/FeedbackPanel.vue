<template>
  <section class="feedback-panel" @click.stop>
    <header><h2>{{ admin ? '用户反馈' : '意见反馈' }}</h2><button :disabled="loading" @click="load">刷新记录</button></header>
    <form v-if="!admin" @submit.prevent="submit">
      <label>反馈类型<select v-model="category"><option>功能建议</option><option>数据问题</option><option>页面问题</option><option>其他</option></select></label>
      <label>反馈内容<textarea v-model="content" required minlength="5" maxlength="2000" rows="5" placeholder="请描述遇到的问题或建议（5—2000字）"></textarea></label>
      <small>{{ content.length }} / 2000</small>
      <label>联系方式（选填）<input v-model="contact" maxlength="120" placeholder="邮箱或其他联系方式"></label>
      <button :disabled="sending || content.trim().length < 5">{{ sending ? '正在提交…' : '提交反馈' }}</button>
    </form>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <router-link v-if="loginRequired" to="/login">登录后提交和查看反馈</router-link>
    <p v-if="notice" class="notice" role="status">{{ notice }}</p>
    <h3>{{ admin ? '全部反馈' : '我的反馈' }} · {{ total }}</h3>
    <p v-if="loading">正在加载…</p><p v-else-if="!items.length && !error">暂无反馈记录</p>
    <article v-for="item in items" :key="item.id">
      <div class="record-header"><strong>{{ item.category }} · #{{ item.id }}</strong><span>{{ item.status === 'handled' ? '已处理' : '待处理' }}</span></div>
      <p v-if="admin">用户：{{ item.username }}（ID {{ item.user_id }}）</p>
      <p class="content">{{ item.content }}</p>
      <p v-if="item.contact">联系方式：{{ item.contact }}</p>
      <small>{{ item.created_at.replace('T',' ').slice(0,19) }}（北京时间）</small>
      <p v-if="item.reply" class="content"><strong>管理员回复：</strong>{{ item.reply }}</p>
      <small v-if="item.replied_at">回复时间：{{ item.replied_at.replace('T',' ').slice(0,19) }}</small>
      <template v-if="admin"><label>回复用户<textarea v-model="item.replyDraft" rows="3" maxlength="2000" placeholder="输入回复，用户可在我的反馈中查看"></textarea></label><button :disabled="saving !== null || !item.replyDraft?.trim()" @click="replyTo(item)">保存回复并标记已处理</button></template>
      <button v-if="admin" :disabled="saving !== null" @click="setStatus(item)">{{ saving === item.id ? '正在保存…' : item.status === 'handled' ? '设为待处理' : '标记已处理' }}</button>
    </article>
    <footer v-if="total > 20"><button :disabled="page === 1 || loading" @click="page--; load()">上一页</button><span>{{ page }} / {{ Math.ceil(total / 20) }}</span><button :disabled="page * 20 >= total || loading" @click="page++; load()">下一页</button></footer>
  </section>
</template>
<script setup>
import { ref, onActivated, onDeactivated } from 'vue'
import axios from 'axios'
const props = defineProps({ admin: Boolean })
const category = ref('功能建议'), content = ref(''), contact = ref(''), items = ref([])
const error = ref(''), notice = ref(''), loginRequired = ref(false)
const loading = ref(false), sending = ref(false), saving = ref(null), page = ref(1), total = ref(0)
let requestId = null, submittedBody = '', revision = 0
const config = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` } })
function fail(err) { loginRequired.value = err.response?.status === 401; error.value = typeof err.response?.data?.detail === 'string' ? err.response.data.detail : '操作失败，请稍后重试' }
async function load() {
  const current = ++revision
  loading.value = true; error.value = ''; loginRequired.value = false; items.value = []
  try { const {data} = await axios.get(props.admin ? '/api/admin/feedback' : '/api/feedback', { ...config(), params: {page: page.value} }); if (current !== revision) return; items.value = data.items.map(item => ({...item, replyDraft: item.reply || ''})); total.value = data.total }
  catch (err) { if (current === revision) { total.value = 0; fail(err) } }
  finally { if (current === revision) loading.value = false }
}
async function submit() {
  if (sending.value) return
  sending.value = true; error.value = notice.value = ''
  const current = revision
  const body = JSON.stringify([category.value, content.value.trim(), contact.value.trim()])
  if (body !== submittedBody || !requestId) { requestId = crypto.randomUUID(); submittedBody = body }
  try {
    await axios.post('/api/feedback', {category: category.value, content: content.value.trim(), contact: contact.value.trim(), request_id: requestId}, config())
    if (current !== revision) return
    content.value = ''; requestId = null; notice.value = '反馈已提交，感谢你的建议'; page.value = 1; await load()
  } catch (err) { if (current === revision) fail(err) }
  finally { sending.value = false }
}
async function replyTo(item) {
  saving.value = item.id
  const current = revision
  try { await axios.put(`/api/admin/feedback/${item.id}`, {status:'handled',reply:item.replyDraft.trim()}, config()); if (current === revision) { notice.value = '回复已保存，用户可在我的反馈中查看'; await load() } }
  catch(err) { if(current === revision) fail(err) }
  finally { saving.value = null }
}
async function setStatus(item) {
  saving.value = item.id
  const current = revision
  try { const {data} = await axios.put(`/api/admin/feedback/${item.id}`, {status: item.status === 'handled' ? 'pending' : 'handled'}, config()); if (current === revision) item.status = data.status }
  catch (err) { if (current === revision) fail(err) }
  finally { saving.value = null }
}
onActivated(() => { page.value = 1; load() })
onDeactivated(() => { revision++; items.value = []; total.value = 0; content.value = contact.value = notice.value = ''; requestId = null })
</script>
<style scoped>
.feedback-panel { padding:20px; border-radius:20px; background:white; color:#334155; margin-bottom:24px; }
header,footer,.record-header { display:flex; justify-content:space-between; align-items:center; gap:12px; }
h2 { font-size:20px; } h3 { font-size:15px; margin-top:24px; }
label { display:block; margin:14px 0 6px; font-size:13px; }
input,textarea,select { display:block; box-sizing:border-box; width:100%; margin-top:8px; padding:12px; border:1px solid #dbe4ef; border-radius:10px; font:inherit; background:#f8fafc; color:#334155; }
button { border:0; border-radius:9px; background:#edf4ff; color:#3977e7; padding:10px 13px; cursor:pointer; } button:disabled { opacity:.5; cursor:default; }
form > button { margin-top:14px; background:#3977e7; color:white; }
article { padding:14px; margin:12px 0; border:1px solid #e5edf7; border-radius:12px; font-size:13px; }
article button { display:block; margin-top:12px; } .content { white-space:pre-wrap; overflow-wrap:anywhere; line-height:1.7; } article p { overflow-wrap:anywhere; }
small { color:#8996aa; font-size:11px; } .error { color:#d94949; } .notice { color:#23825b; }
</style>
