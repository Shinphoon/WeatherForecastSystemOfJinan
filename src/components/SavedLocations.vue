<template>
  <section class="saved-locations" aria-label="已保存地点">
    <div class="location-strip">
      <button class="add-location" :disabled="busy || locations.length >= 5" @click="showAdd=!showAdd">＋</button>
      <button v-for="place in locations" :key="place.id" class="place"
        :class="{active: activeId === place.id}" @click="select(place)">
        <span>📍 {{ place.name }}</span><small>{{ place.station_name || place.address }}</small>
        <i @click.stop="remove(place)" aria-label="删除地点">×</i>
      </button>
      <span class="count">{{ locations.length }}/5</span>
    </div>
    <div v-if="showAdd" class="add-panel">
      <form @submit.prevent="search"><input v-model="query" maxlength="60" placeholder="搜索山东省内地点" /><button :disabled="busy">搜索</button></form>
      <button class="current" :disabled="busy" @click="addCurrent">📍 保存当前定位</button>
      <button v-for="result in results" :key="`${result.lng},${result.lat}`" class="result" @click="saveResult(result)">
        <strong>{{ result.name }}</strong><small>{{ result.address }}</small>
      </button>
    </div>
    <p v-if="message" role="status">{{ message }}</p>
  </section>
</template>
<script setup>
import { onMounted, ref, watch } from 'vue'
import axios from 'axios'
const props=defineProps({currentLocation:{type:Object,default:()=>({})}})
const emit=defineEmits(['selected'])
const locations=ref([]), activeId=ref(null), busy=ref(false), message=ref('')
const showAdd=ref(false), query=ref(''), results=ref([])
const config=()=>({headers:{Authorization:`Bearer ${localStorage.getItem('access_token')||''}`}})
async function load(){
  if(!localStorage.getItem('access_token')) return
  try {const {data}=await axios.get('/api/auth/locations',config());locations.value=data.locations;syncActive()}
  catch(err){message.value=err.response?.status===401?'登录后可保存地点':'保存地点加载失败'}
}
function syncActive(){
  const lng=Number(props.currentLocation?.lng),lat=Number(props.currentLocation?.lat)
  activeId.value=Number.isFinite(lng)&&Number.isFinite(lat)?locations.value.find(p=>Math.abs(p.lng-lng)<.0001&&Math.abs(p.lat-lat)<.0001)?.id||null:null
}
function browserLocation(){return new Promise((resolve,reject)=>navigator.geolocation?.getCurrentPosition(resolve,reject,{enableHighAccuracy:true,timeout:10000,maximumAge:30000})||reject(new Error('当前浏览器不支持定位')))}
async function addCurrent(){
  busy.value=true;message.value='正在定位…'
  try {
    const position=await browserLocation()
    const name=window.prompt('给这个地点起个名字（可留空）','')
    if(name===null)return
    const {data}=await axios.post('/api/auth/locations',{lng:position.coords.longitude,lat:position.coords.latitude,name:name.trim()},config())
    await load(); await select(data.location); message.value='地点已保存'
  } catch(err){message.value=err.response?.data?.detail||err.message||'保存失败'}
  finally{busy.value=false}
}
async function search(){
  if(query.value.trim().length<2){message.value='请输入至少2个字的地点名称';return}
  busy.value=true;message.value='正在搜索…'
  try {const {data}=await axios.get('/api/auth/locations/search',{...config(),params:{q:query.value.trim()}});results.value=data.results;message.value=results.value.length?'':'没有找到山东省内的匹配地点'}
  catch(err){message.value=err.response?.data?.detail||'搜索失败'}finally{busy.value=false}
}
async function saveResult(result){
  busy.value=true
  try {const {data}=await axios.post('/api/auth/locations',{lng:result.lng,lat:result.lat,name:result.name},config());await load();showAdd.value=false;results.value=[];await select(data.location);message.value='地点已保存'}
  catch(err){message.value=err.response?.data?.detail||'保存失败'}finally{busy.value=false}
}
async function select(place){
  if(busy.value)return
  busy.value=true
  try {const {data}=await axios.put(`/api/auth/locations/${place.id}/select`,{},config());activeId.value=place.id;message.value='';emit('selected',data)}
  catch(err){message.value=err.response?.data?.detail||'切换地点失败'}
  finally{busy.value=false}
}
async function remove(place){
  if(!window.confirm(`删除“${place.name}”？`))return
  busy.value=true
  try {await axios.delete(`/api/auth/locations/${place.id}`,config());if(activeId.value===place.id)activeId.value=null;await load();message.value='地点已删除'}
  catch(err){message.value=err.response?.data?.detail||'删除失败'}finally{busy.value=false}
}
onMounted(load)
watch(()=>[props.currentLocation?.lng,props.currentLocation?.lat],syncActive)
</script>
<style scoped>
.saved-locations{padding:0 20px 12px}.location-strip{display:flex;gap:8px;align-items:stretch;overflow-x:auto;padding:4px 0 8px}.add-location{flex:0 0 42px;border:1px dashed #8db4ff;border-radius:14px;background:#fff;color:#3977e7;font-size:24px}.place{position:relative;flex:0 0 150px;text-align:left;border:1px solid #dfe8f5;border-radius:14px;background:#fff;padding:10px 25px 10px 11px;color:#334155}.place.active{border-color:#3977e7;background:#edf4ff}.place span,.place small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.place small{margin-top:4px;color:#94a3b8}.place i{position:absolute;right:7px;top:7px;font-style:normal;color:#94a3b8;font-size:17px}.count{align-self:center;color:#94a3b8;font-size:12px;white-space:nowrap}.saved-locations p{margin:0;color:#b45309;font-size:12px}button{cursor:pointer}button:disabled{opacity:.5}
.add-panel{background:white;border:1px solid #dfe8f5;border-radius:14px;padding:10px;margin-bottom:8px}.add-panel form{display:flex;gap:8px}.add-panel input{min-width:0;flex:1;padding:10px;border:1px solid #dbe4ef;border-radius:9px;font:inherit}.add-panel button{border:0;border-radius:9px;padding:9px 12px;background:#edf4ff;color:#3977e7}.add-panel .current{margin:8px 0;width:100%;text-align:left}.result{display:block!important;width:100%;text-align:left;margin-top:6px}.result strong,.result small{display:block}.result small{color:#94a3b8;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
</style>
