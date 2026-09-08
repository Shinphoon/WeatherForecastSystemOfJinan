<template>
  <div class="weather-card">
    <div class="weather-title">{{ stationName }}国家气象站</div>
    <div class="station">站号 {{ weather.station || stationId }}</div>
    <div v-if="loading" class="loading">正在加载天气数据...</div>
    <div v-else-if="error" class="error">天气数据加载失败</div>
    <div v-else>
      <div class="temperature">{{ weather.temperature ?? '--' }}℃</div>
      <div class="weather-grid">
        <div class="item">
          <span class="label">湿度</span>
          <span class="value">{{ weather.humidity ?? '--' }}%</span>
        </div>
        <div class="item">
          <span class="label">风速</span>
          <span class="value">{{ cleanWindSpeed }} m/s</span>
        </div>
        <div class="item">
          <span class="label">气压</span>
          <span class="value">{{ weather.pressure ?? '--' }} hPa</span>
        </div>
        <div class="item">
          <span class="label">能见度</span>
          <span class="value">{{ weather.visibility ?? '--' }} km</span>
        </div>
        <div class="item">
          <span class="label">1小时降水</span>
          <span class="value">{{ weather.rain_1h ?? '--' }} mm</span>
        </div>
        <div class="item">
          <span class="label">24小时降水</span>
          <span class="value">{{ weather.rain_24h ?? '--' }} mm</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getStationRealtimeWeather } from '../api/weather'

const props = defineProps({
  stationId: {
    type: String,
    default: '54823'
  },
  stationName: {
    type: String,
    default: '济南'
  }
})

const weather = ref({})
const loading = ref(true)
const error = ref(false)

const cleanWindSpeed = computed(() => {
  if (!weather.value.wind_speed) return '--'
  return String(weather.value.wind_speed)
    .replace('(', '')
    .replace(')', '')
})

async function loadWeather() {
  loading.value = true
  error.value = false
  try {
    const response = await getStationRealtimeWeather(props.stationId)
    weather.value = response.data
  } catch (err) {
    console.error('实时天气加载失败：', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

watch(
  () => props.stationId,
  () => {
    loadWeather()
  },
  { immediate: true }
)
</script>

<style scoped>
.weather-card {
  background: white;
  border-radius: 22px;
  padding: 22px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.08);
}
.weather-title {
  font-size: 18px;
  font-weight: 600;
}
.station {
  margin-top: 4px;
  color: #888;
  font-size: 13px;
}
.temperature {
  font-size: 52px;
  font-weight: 600;
  margin: 20px 0;
}
.weather-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.item {
  background: #f5f7fa;
  border-radius: 14px;
  padding: 14px;
}
.label {
  display: block;
  font-size: 13px;
  color: #888;
}
.value {
  display: block;
  margin-top: 5px;
  font-size: 17px;
  font-weight: 500;
}
.loading {
  padding: 25px 0;
  color: #888;
}
.error {
  padding: 25px 0;
  color: #e5484d;
}
</style>