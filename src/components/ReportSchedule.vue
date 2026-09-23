<template>
  <section class="report-settings">
    <h2>天气报告</h2>
    <p>北京时间，到点自动发送到消息中心；已绑定邮箱且开启邮件推送时同时发送邮件。无需保持登录。</p>
    <form @submit.prevent="save">
      <div v-for="period in periods" :key="period.key" class="report-row">
        <button type="button" class="toggle" :class="{on: period.enabled.value}" role="switch"
          :aria-checked="period.enabled.value" @click="period.enabled.value = !period.enabled.value">
          <span>{{ period.enabled.value ? 'ON' : 'OFF' }}</span><i></i>
        </button>
        <label>{{ period.label }}（{{ period.min }}—{{ period.max }}）
          <input v-model="period.time.value" type="time" :min="period.min" :max="period.max" required
            :disabled="loading || !period.enabled.value" />
        </label>
      </div>
      <p>早报、午报介绍当天的天气，晚报提前提示明日天气。关闭后该时段不会生成消息或邮件。</p>
      <button :disabled="loading || saving">{{ saving ? '保存中…' : '保存报告设置' }}</button>
    </form>
    <p role="status">{{ message }}</p>
  </section>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const morning=ref('07:00'), noon=ref('15:20'), evening=ref('18:00')
const morningEnabled=ref(true), noonEnabled=ref(true), eveningEnabled=ref(true)
const loading=ref(true), saving=ref(false), message=ref('')
const periods=[
  {key:'morning',label:'早间天气报告',min:'05:00',max:'11:00',time:morning,enabled:morningEnabled},
  {key:'noon',label:'午间天气报告',min:'11:00',max:'16:30',time:noon,enabled:noonEnabled},
  {key:'evening',label:'晚间天气报告',min:'16:30',max:'22:30',time:evening,enabled:eveningEnabled}
]
const config=()=>({headers:{Authorization:`Bearer ${localStorage.getItem('access_token') || ''}`}})
onMounted(async()=>{
  try {
    const {data}=await axios.get('/api/auth/report-schedule',config())
    morning.value=data.morning; noon.value=data.noon; evening.value=data.evening
    morningEnabled.value=!!data.morning_enabled; noonEnabled.value=!!data.noon_enabled; eveningEnabled.value=!!data.evening_enabled
  } catch { message.value='报告设置加载失败，请刷新后重试' }
  finally { loading.value=false }
})
async function save(){
  if(morning.value<'05:00'||morning.value>'11:00'||noon.value<'11:00'||noon.value>'16:30'||evening.value<'16:30'||evening.value>'22:30'){
    message.value='请选择规定范围内的时间'; return
  }
  saving.value=true
  try {
    await axios.put('/api/auth/report-schedule',{morning:morning.value,noon:noon.value,evening:evening.value,
      morning_enabled:morningEnabled.value,noon_enabled:noonEnabled.value,evening_enabled:eveningEnabled.value},config())
    message.value='报告设置已保存；当日已经发出的报告不会重复发送'
  } catch(err){ message.value=typeof err.response?.data?.detail==='string'?err.response.data.detail:'保存失败，请重试' }
  finally { saving.value=false }
}
</script>
<style scoped>
.report-settings{background:white;border-radius:22px;padding:20px;margin-top:20px;color:#334155}h2{font-size:19px}p{font-size:13px;line-height:1.7;color:#64748b}label{display:block;font-size:14px}input{display:block;margin-top:8px;padding:10px;border:1px solid #dbe4ef;border-radius:10px;font:inherit}button{padding:12px 18px;background:#3977e7;color:white;border:0;border-radius:10px;cursor:pointer}button:disabled{opacity:.5}.report-row{display:flex;align-items:center;gap:16px;margin:16px 0}.report-row label{flex:1}.toggle{position:relative;width:76px;height:36px;padding:0 9px;border-radius:20px;background:#94a3b8;text-align:right;font-size:11px}.toggle i{position:absolute;left:4px;top:4px;width:28px;height:28px;border-radius:50%;background:white;box-shadow:0 2px 6px #0003;transition:.2s}.toggle.on{background:#3977e7;text-align:left}.toggle.on i{left:44px}.toggle span{font-weight:700}
</style>
