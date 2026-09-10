<template>
  <div class="forecast-page">
    <header class="forecast-header">
      <div>
        <h1>天气预报</h1>
        <p>{{ selectedStation.name }} · 短时 / 24小时 / 7天</p>
      </div>
      <div class="station-wrap">
        <button class="station-badge" @click="selectorOpen = !selectorOpen">📍 {{ selectedStation.name }} ▼</button>
        <div v-if="selectorOpen" class="station-menu">
          <button v-for="station in stationOptions" :key="station.id" :class="{selected:station.id===selectedStationId}" @click="selectStation(station)">
            {{ station.name }} · {{ station.id }}
          </button>
        </div>
      </div>
    </header>

    <section class="section">
      <div class="section-title">
        <div><h2>未来2小时</h2><p>{{ selectedStation.name }}站 · 短时天气趋势</p></div>
        <span class="update-tag">实时更新</span>
      </div>
      <div v-if="shortLoading" class="loading-card">正在加载{{ selectedStation.name }}站短时天气预报...</div>
      <div v-else-if="shortError" class="error-card">{{ shortError }}</div>
      <div v-else class="short-card">
        <div class="short-icon">{{ shortForecastIcon }}</div>
        <div class="short-content"><div class="short-main">未来2小时</div><div class="short-description">{{ shortForecastText }}</div></div>
      </div>
    </section>

    <section class="section">
      <div class="section-title">
        <div><h2>未来24小时</h2><p>{{ selectedStation.name }}站 · 逐小时天气趋势</p></div>
        <span class="scroll-hint">← 左右滑动 →</span>
      </div>
      <div v-if="hourlyLoading" class="loading-card">正在加载{{ selectedStation.name }}站24小时天气预报...</div>
      <div v-else-if="hourlyError" class="error-card">{{ hourlyError }}</div>
      <div v-else class="hourly-card">
        <div v-for="item in hourlyForecast" :key="item.fullTime" class="hour-item">
          <div class="hour-time">{{ item.time }}</div>
          <div class="hour-icon">{{ item.icon }}</div>
          <div class="hour-temp">{{ item.temperature }}℃</div>
          <div class="hour-weather">{{ item.weather }}</div>
          <div class="hour-rain">💧 {{ item.rain }}%</div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-title"><div><h2>24小时天气要素</h2><p>{{ selectedStation.name }}站 · 预报时段综合统计</p></div></div>
      <div class="element-grid">
        <div class="element-card"><div class="element-icon">🌡️</div><div><div class="element-label">最高气温</div><div class="element-value">{{ maxTemperature }}℃</div></div></div>
        <div class="element-card"><div class="element-icon">❄️</div><div><div class="element-label">最低气温</div><div class="element-value">{{ minTemperature }}℃</div></div></div>
        <div class="element-card"><div class="element-icon">💧</div><div><div class="element-label">最大降水概率</div><div class="element-value">{{ maxRainProbability }}%</div></div></div>
        <div class="element-card"><div class="element-icon">💨</div><div><div class="element-label">最大风速</div><div class="element-value">{{ maxWindSpeed }} km/h</div></div></div>
      </div>
    </section>

    <section class="section">
      <div class="section-title">
        <div><h2>未来7天</h2><p>{{ selectedStation.name }}站 · 中期天气趋势</p></div>
        <span class="data-source">Open-Meteo</span>
      </div>
      <div v-if="dailyLoading" class="loading-card">正在加载{{ selectedStation.name }}站7天天气预报...</div>
      <div v-else-if="dailyError" class="error-card">{{ dailyError }}</div>
      <div v-else class="daily-list">
        <div v-for="item in sevenDayForecast" :key="item.fullDate" class="daily-item">
          <div class="daily-date"><div class="weekday">{{ item.week }}</div><div class="date">{{ item.date }}</div></div>
          <div class="daily-weather">
            <div class="daily-icon">{{ item.icon }}</div>
            <div><div class="daily-condition">{{ item.weather }}</div><div class="daily-rain">💧 {{ item.rain }}%</div></div>
          </div>
          <div class="daily-temp"><strong>{{ item.max }}°</strong><span> / {{ item.min }}°</span></div>
        </div>
      </div>
    </section>

    <section v-if="sevenDayForecast.length>0" class="section">
      <div class="section-title"><div><h2>降水与风</h2><p>{{ selectedStation.name }}站 · 未来7天预报详情</p></div></div>
      <div class="detail-list">
        <div v-for="item in sevenDayForecast" :key="`${item.fullDate}-detail`" class="detail-item">
          <div class="detail-date">{{ item.week }}</div>
          <div class="detail-value">🌧 {{ item.rainAmount }} mm</div>
          <div class="detail-value">💨 {{ item.maxWind }} km/h</div>
        </div>
      </div>
    </section>
    <div class="bottom-space"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getStations,
  getForecast2h,
  getForecast24h,
  getForecast7d
} from '../api/weather'

const stationOptions = ref([])
const savedStationId = localStorage.getItem('selectedStationId')
const selectedStationId = ref(savedStationId || '54823')
const selectorOpen = ref(false)

const selectedStation = computed(() => {
  return (
    stationOptions.value.find(
      item => item.id === selectedStationId.value
    ) || {
      id: selectedStationId.value,
      name: '济南'
    }
  )
})

const shortForecastText = ref('')
const shortForecastIcon = ref('🌤')
const shortLoading = ref(true)
const shortError = ref('')
const hourlyForecast = ref([])
const hourlyLoading = ref(true)
const hourlyError = ref('')
const sevenDayForecast = ref([])
const dailyLoading = ref(true)
const dailyError = ref('')

function getWeatherIcon(code) {
  if (code===0) return '☀️'
  if (code===1||code===2) return '🌤'
  if (code===3) return '☁️'
  if (code===45||code===48) return '🌫️'
  if (code>=51&&code<=57) return '🌦️'
  if (code>=61&&code<=67) return '🌧️'
  if (code>=71&&code<=77) return '🌨️'
  if (code>=80&&code<=82) return '🌦️'
  if (code>=85&&code<=86) return '🌨️'
  if (code>=95&&code<=99) return '⛈️'
  return '☁️'
}
function getWeatherText(code) {
  if (code===0) return '晴'
  if (code===1) return '大部晴朗'
  if (code===2) return '多云'
  if (code===3) return '阴'
  if (code===45||code===48) return '雾'
  if ([51,53,55].includes(code)) return '毛毛雨'
  if ([56,57].includes(code)) return '冻毛毛雨'
  if ([61,63,65].includes(code)) return '雨'
  if ([66,67].includes(code)) return '冻雨'
  if ([71,73,75,77].includes(code)) return '降雪'
  if ([80,81,82].includes(code)) return '阵雨'
  if ([85,86].includes(code)) return '阵雪'
  if (code===95) return '雷暴'
  if (code===96||code===99) return '雷暴伴冰雹'
  return '未知'
}
function formatHour(time) {
  return time ? time.slice(11,16) : '--:--'
}
function getWeekday(dateString,index) {
  if (index===0) return '今天'
  if (index===1) return '明天'
  const weekdays=['周日','周一','周二','周三','周四','周五','周六']
  return weekdays[new Date(`${dateString}T00:00:00`).getDay()]
}
function validValues(key) {
  return hourlyForecast.value.map(item=>item[key]).filter(value=>value!==null&&value!==undefined&&!Number.isNaN(Number(value))).map(Number)
}
const maxTemperature = computed(()=>{
  const v=validValues('rawTemperature')
  return v.length?Math.round(Math.max(...v)):'--'
})
const minTemperature = computed(()=>{
  const v=validValues('rawTemperature')
  return v.length?Math.round(Math.min(...v)):'--'
})
const maxRainProbability = computed(()=>{
  const v=validValues('rain')
  return v.length?Math.max(...v):'--'
})
const maxWindSpeed = computed(()=>{
  const v=validValues('rawWindSpeed')
  return v.length?Math.max(...v).toFixed(1):'--'
})

async function loadForecast2h() {
  shortLoading.value=true
  shortError.value=''
  try {
    const {data}=await getForecast2h(selectedStationId.value)
    shortForecastText.value=data.text||'暂无短时天气预报数据'
    if (data.hours?.length) shortForecastIcon.value=getWeatherIcon(data.hours[0].weather_code)
  } catch (error) {
    console.error('短时天气加载失败：',error)
    shortError.value='短时天气预报加载失败'
  } finally {
    shortLoading.value=false
  }
}
async function loadForecast24h() {
  hourlyLoading.value=true
  hourlyError.value=''
  try {
    const {data}=await getForecast24h(selectedStationId.value)
    hourlyForecast.value=data.map(item=>({
      fullTime:item.time,
      time:formatHour(item.time),
      temperature:Math.round(item.temperature),
      rawTemperature:item.temperature,
      weatherCode:item.weather_code,
      weather:getWeatherText(item.weather_code),
      icon:getWeatherIcon(item.weather_code),
      rain:item.precipitation_probability??0,
      precipitation:item.precipitation??0,
      humidity:item.humidity??0,
      pressure:item.pressure??0,
      rawWindSpeed:item.wind_speed??0,
      windDirection:item.wind_direction??0
    }))
  } catch (error) {
    console.error('24小时天气加载失败：',error)
    hourlyForecast.value=[]
    hourlyError.value='24小时天气预报加载失败'
  } finally {
    hourlyLoading.value=false
  }
}
async function loadForecast7d() {
  dailyLoading.value=true
  dailyError.value=''
  try {
    const {data}=await getForecast7d(selectedStationId.value)
    sevenDayForecast.value=data.map((item,index)=>({
      fullDate:item.date,
      week:getWeekday(item.date,index),
      date:item.date.slice(5).replace('-','/'),
      weatherCode:item.weather_code,
      weather:getWeatherText(item.weather_code),
      icon:getWeatherIcon(item.weather_code),
      max:Math.round(item.temperature_max),
      min:Math.round(item.temperature_min),
      rain:item.precipitation_probability??0,
      rainAmount:item.precipitation_sum??0,
      maxWind:item.wind_speed_max??0
    }))
  } catch (error) {
    console.error('7天天气加载失败：',error)
    sevenDayForecast.value=[]
    dailyError.value='7天天气预报加载失败'
  } finally {
    dailyLoading.value=false
  }
}
async function loadAllForecasts() {
  await Promise.all([loadForecast2h(),loadForecast24h(),loadForecast7d()])
}
function selectStation(station) {
  selectedStationId.value=station.id
  selectorOpen.value=false
  localStorage.setItem('selectedStationId',station.id)
  loadAllForecasts()
}

async function loadStationOptions() {
  try {
    const response = await getStations()

    stationOptions.value = response.data.map(
      station => ({
        id: station.station || station.id,
        name: station.name
      })
    )

    const stationExists =
      stationOptions.value.some(
        item =>
          item.id === selectedStationId.value
      )

    if (!stationExists) {
      selectedStationId.value = '54823'

      localStorage.setItem(
        'selectedStationId',
        '54823'
      )
    }
  } catch (err) {
    console.error(
      '站点列表加载失败：',
      err
    )
  }
}

onMounted(async () => {
  await loadStationOptions()
  await loadAllForecasts()
})
</script>

<style scoped>
.forecast-page{width:100%;min-height:100vh;box-sizing:border-box;padding:22px 16px 110px;background:linear-gradient(180deg,#eaf4ff 0%,#f5f8fc 300px,#f5f7fa 100%)}
.forecast-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:26px}
.forecast-header h1{margin:0;font-size:30px;line-height:1.2;color:#1e293b}
.forecast-header p{margin:7px 0 0;font-size:13px;color:#94a3b8}
.station-wrap{position:relative}
.station-badge{flex-shrink:0;padding:9px 13px;border:none;border-radius:20px;background:white;font-size:13px;color:#3b82f6;box-shadow:0 5px 15px rgba(15,23,42,.06);cursor:pointer}
.station-menu{position:absolute;top:44px;right:0;z-index:100;width:170px;padding:7px;border-radius:14px;background:white;box-shadow:0 8px 24px rgba(15,23,42,.15)}
.station-menu button{display:block;width:100%;padding:9px 10px;border:none;border-radius:9px;background:transparent;text-align:left;color:#475569;cursor:pointer}
.station-menu button:hover,.station-menu button.selected{background:#eef5ff;color:#267cff}
.section{margin-bottom:27px}
.section-title{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:12px}
.section-title h2{margin:0;font-size:20px;color:#1e293b}
.section-title p{margin:4px 0 0;font-size:12px;color:#94a3b8}
.update-tag,.scroll-hint,.data-source{font-size:11px;color:#3b82f6}
.loading-card,.error-card{padding:22px;border-radius:20px;background:white;font-size:13px;color:#64748b;box-shadow:0 7px 18px rgba(15,23,42,.05)}
.error-card{color:#ef4444}
.short-card{display:flex;align-items:center;gap:16px;padding:20px;border-radius:22px;background:white;box-shadow:0 8px 22px rgba(15,23,42,.06)}
.short-icon{width:64px;height:64px;display:flex;align-items:center;justify-content:center;flex-shrink:0;border-radius:19px;background:#eef5ff;font-size:31px}
.short-content{min-width:0}
.short-main{margin-bottom:7px;font-size:18px;font-weight:700;color:#334155}
.short-description{font-size:13px;line-height:1.7;color:#64748b}
.hourly-card{display:flex;gap:10px;overflow-x:auto;padding:16px;border-radius:22px;background:white;box-shadow:0 8px 22px rgba(15,23,42,.05);scrollbar-width:none}
.hourly-card::-webkit-scrollbar{display:none}
.hour-item{flex:0 0 76px;box-sizing:border-box;padding:13px 5px;border-radius:17px;text-align:center;background:#f7f9fc}
.hour-time{font-size:12px;color:#94a3b8}
.hour-icon{margin:11px 0 8px;font-size:27px}
.hour-temp{font-size:17px;font-weight:700;color:#334155}
.hour-weather{margin-top:4px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-size:10px;color:#94a3b8}
.hour-rain{margin-top:7px;font-size:10px;color:#60a5fa}
.element-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.element-card{display:flex;align-items:center;gap:11px;min-width:0;padding:15px;border-radius:18px;background:white;box-shadow:0 6px 17px rgba(15,23,42,.04)}
.element-icon{flex-shrink:0;font-size:23px}
.element-label{font-size:11px;color:#94a3b8}
.element-value{margin-top:4px;font-size:15px;font-weight:700;color:#334155}
.daily-list{overflow:hidden;border-radius:22px;background:white;box-shadow:0 8px 22px rgba(15,23,42,.05)}
.daily-item{display:grid;grid-template-columns:72px minmax(0,1fr) 80px;align-items:center;gap:8px;padding:15px 16px;border-bottom:1px solid #f1f5f9}
.daily-item:last-child{border-bottom:none}
.weekday{font-size:14px;font-weight:700;color:#334155}
.date{margin-top:4px;font-size:11px;color:#94a3b8}
.daily-weather{display:flex;align-items:center;gap:9px;min-width:0}
.daily-icon{flex-shrink:0;font-size:25px}
.daily-condition{font-size:13px;color:#475569}
.daily-rain{margin-top:3px;font-size:10px;color:#60a5fa}
.daily-temp{text-align:right;white-space:nowrap;font-size:14px}
.daily-temp strong{color:#ef4444}
.daily-temp span{color:#60a5fa}
.detail-list{overflow:hidden;border-radius:20px;background:white;box-shadow:0 7px 20px rgba(15,23,42,.05)}
.detail-item{display:grid;grid-template-columns:65px 1fr 1fr;align-items:center;gap:8px;padding:13px 15px;border-bottom:1px solid #f1f5f9}
.detail-item:last-child{border-bottom:none}
.detail-date{font-size:13px;font-weight:600;color:#334155}
.detail-value{font-size:11px;color:#64748b}
.bottom-space{height:30px}
@media(max-width:380px){.forecast-header h1{font-size:27px}.station-badge{padding:8px 10px}.daily-item{grid-template-columns:62px minmax(0,1fr) 70px;padding:14px 12px}.detail-item{grid-template-columns:55px 1fr 1fr;padding:12px 10px}}
</style>
