<template>
  <div class="reality-page">
    <header class="page-header">
      <div>
        <h1>天气实况</h1>
        <div class="station-row">
          <button class="station-selector" @click="selectorOpen = !selectorOpen">
            {{ selectedStation.name }}国家气象站 · {{ selectedStation.id }} ▼
          </button>
          <div v-if="selectorOpen" class="station-menu">
            <button
              v-for="station in stationOptions"
              :key="station.id"
              :class="{ selected: station.id === selectedStationId }"
              @click="selectStation(station)"
            >
              {{ station.name }} · {{ station.id }}
            </button>
          </div>
        </div>
      </div>
      <div class="live-badge">
        <span class="live-dot"></span>
        实时
      </div>
    </header>

    <section class="current-card">
      <div v-if="loading">正在加载{{ selectedStation.name }}站实况数据...</div>
      <div v-else-if="error" class="error">实况数据加载失败</div>
      <template v-else>
        <div class="current-top">
          <div>
            <div class="current-label">当前温度</div>
            <div class="current-temp">{{ realtime.temperature ?? '--' }}℃</div>
          </div>
          <div class="current-info">
            <div>湿度 <strong>{{ realtime.humidity ?? '--' }}%</strong></div>
            <div>气压 <strong>{{ realtime.pressure ?? '--' }} hPa</strong></div>
          </div>
        </div>
      </template>
    </section>

    <section class="element-tabs">
      <button
        v-for="item in elements"
        :key="item.key"
        :class="{ active: activeElement === item.key }"
        @click="changeElement(item.key)"
      >
        {{ item.name }}
      </button>
    </section>

    <section class="chart-card">
      <div class="chart-header">
        <div>
          <h2>{{ currentTitle }}</h2>
          <p>{{ selectedStation.name }}站 · 近24小时逐小时观测</p>
        </div>
      </div>
      <div v-if="chartLoading" class="chart-message">正在加载图表...</div>
      <div v-else-if="error" class="chart-message">暂无可用数据</div>
      <div v-else ref="chartRef" class="chart"></div>
    </section>

    <section class="detail-card">
      <div class="detail-title">最新观测</div>
      <div class="detail-grid">
        <div class="detail-item">
          <span>风向</span>
          <strong>{{ cleanWindDirection }}</strong>
        </div>
        <div class="detail-item">
          <span>风速</span>
          <strong>{{ cleanWindSpeed }} m/s</strong>
        </div>
        <div class="detail-item">
          <span>1小时降水</span>
          <strong>{{ realtime.rain_1h ?? '--' }} mm</strong>
        </div>
        <div class="detail-item">
          <span>24小时降水</span>
          <strong>{{ realtime.rain_24h ?? '--' }} mm</strong>
        </div>
        <div class="detail-item">
          <span>能见度</span>
          <strong>{{ realtime.visibility ?? '--' }} km</strong>
        </div>
        <div class="detail-item">
          <span>站号</span>
          <strong>{{ realtime.station ?? selectedStation.id }}</strong>
        </div>
      </div>
    </section>
    <div class="bottom-space"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import {
  getStations,
  getStationRealtimeWeather,
  getStationTodayWeather
} from '../api/weather'

const stationOptions = ref([])

const savedStationId = localStorage.getItem('selectedStationId')
const selectedStationId = ref(
  savedStationId || '54823'
)
const selectorOpen = ref(false)
const realtime = ref({})
const historyData = ref([])
const loading = ref(true)
const chartLoading = ref(true)
const error = ref(false)
const activeElement = ref('temperature')
const chartRef = ref(null)
let chartInstance = null

const selectedStation = computed(() => {
  return (
    stationOptions.value.find(
      item => item.id === selectedStationId.value
    ) || stationOptions.value[0] || {
      id: selectedStationId.value,
      name: '济南'
    }
  )
})

const elements = [
  { key: 'temperature', name: '温度' },
  { key: 'humidity', name: '湿度' },
  { key: 'pressure', name: '气压' },
  { key: 'wind_speed', name: '风速' }
]

const elementConfig = {
  temperature: {
    title: '近24小时气温变化',
    unit: '℃',
    seriesName: '气温'
  },
  humidity: {
    title: '近24小时相对湿度变化',
    unit: '%',
    seriesName: '相对湿度'
  },
  pressure: {
    title: '近24小时气压变化',
    unit: 'hPa',
    seriesName: '气压'
  },
  wind_speed: {
    title: '近24小时风速变化',
    unit: 'm/s',
    seriesName: '风速'
  }
}

const currentTitle = computed(() => {
  return elementConfig[activeElement.value].title
})

const cleanWindSpeed = computed(() => {
  if (!realtime.value.wind_speed) return '--'
  return String(realtime.value.wind_speed)
    .replace('(', '')
    .replace(')', '')
})

const cleanWindDirection = computed(() => {
  if (!realtime.value.wind_direction) return '--'
  return String(realtime.value.wind_direction)
    .replace('(', '')
    .replace(')', '')
})

function formatTime(time) {
  if (!time) return ''
  const parts = time.split(' ')
  return parts.length >= 2 ? parts[1] : time
}

function drawChart() {
  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value)

  const config = elementConfig[activeElement.value]
  const sortedData = [...historyData.value].reverse()
  const times = sortedData.map(item => formatTime(item.time))
  const values = sortedData.map(item => {
    const value = Number(item[activeElement.value])
    return Number.isNaN(value) ? null : value
  })

  const isPressure = activeElement.value === 'pressure'
  const option = {
    tooltip: {
    trigger: 'axis',
    triggerOn: 'mousemove',
    enterable: true,
    alwaysShowContent: false,
    hideDelay: 300,
    axisPointer: {
      type: 'line',
      snap: true
    },
    formatter(params) {
      const item = params[0]
      return `${item.axisValue}<br>${config.seriesName}：${item.value} ${config.unit}`
    }
  },
    grid: {
      left: isPressure ? 58 : 42,
      right: 18,
      top: 30,
      bottom: 40
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLabel: {
        fontSize: 10,
        interval: 2
      }
    },
    yAxis: {
      type: 'value',
      min: isPressure ? 975 : undefined,
      max: isPressure ? 1025 : undefined,
      interval: isPressure ? 10 : undefined,
      axisLabel: {
        fontSize: 10,
        formatter: value => {
          return isPressure ? `${value} hPa` : `${value} ${config.unit}`
        }
      },
      splitLine: {
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: config.seriesName,
        type: 'line',
        smooth: true,
        data: values,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        lineStyle: {
          width: 3
        },
        areaStyle: {
          opacity: 0.08
        }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

function changeElement(key) {
  activeElement.value = key
  drawChart()
}

async function selectStation(station) {
  selectedStationId.value = station.id
  selectorOpen.value = false
  localStorage.setItem('selectedStationId', station.id)
  await loadWeatherData()
}

function handleResize() {
  if (chartInstance) chartInstance.resize()
}

async function loadWeatherData() {
  try {
    loading.value = true
    chartLoading.value = true
    error.value = false

    const [realtimeResponse, todayResponse] = await Promise.all([
      getStationRealtimeWeather(selectedStationId.value),
      getStationTodayWeather(selectedStationId.value)
    ])

    realtime.value = realtimeResponse.data
    historyData.value = todayResponse.data
    chartLoading.value = false

    await nextTick()

    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }

    drawChart()
  } catch (err) {
    console.error(`${selectedStation.value.name}站实况数据加载失败：`, err)
    realtime.value = {}
    historyData.value = []
    error.value = true
    chartLoading.value = false
  } finally {
    loading.value = false
  }
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
  } catch (err) {
    console.error(
      '站点列表加载失败：',
      err
    )
  }
}

onMounted(async () => {
  await loadStationOptions()
  await loadWeatherData()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.reality-page {
  min-height: 100vh;
  padding: 20px 16px;
  box-sizing: border-box;
  background: linear-gradient(180deg,#eaf4ff 0%,#f5f7fa 320px,#f5f7fa 100%);
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 18px;
}
.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: #1e293b;
}
.station-row {
  position: relative;
  margin-top: 5px;
}
.station-selector {
  padding: 0;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
}
.station-menu {
  position: absolute;
  top: 27px;
  left: 0;
  z-index: 100;
  width: 180px;
  padding: 7px;
  border-radius: 14px;
  background: white;
  box-shadow: 0 8px 24px rgba(15,23,42,.15);
}
.station-menu button {
  display: block;
  width: 100%;
  padding: 9px 10px;
  border: none;
  border-radius: 9px;
  background: transparent;
  text-align: left;
  color: #475569;
  cursor: pointer;
}
.station-menu button:hover,
.station-menu button.selected {
  background: #eef5ff;
  color: #267cff;
}
.live-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 11px;
  border-radius: 18px;
  background: white;
  color: #267cff;
  font-size: 12px;
}
.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2ecc71;
}
.current-card {
  margin-bottom: 16px;
  padding: 19px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 6px 18px rgba(0,0,0,.06);
}
.current-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.current-label {
  color: #94a3b8;
  font-size: 12px;
}
.current-temp {
  margin-top: 5px;
  font-size: 42px;
  font-weight: 600;
}
.current-info {
  text-align: right;
  color: #64748b;
  font-size: 12px;
  line-height: 2;
}
.current-info strong {
  margin-left: 5px;
  color: #334155;
  font-size: 14px;
}
.element-tabs {
  display: grid;
  grid-template-columns: repeat(4,1fr);
  gap: 7px;
  margin-bottom: 14px;
}
.element-tabs button {
  padding: 10px 4px;
  border: none;
  border-radius: 12px;
  background: white;
  color: #64748b;
  cursor: pointer;
  font-size: 13px;
}
.element-tabs button.active {
  background: #267cff;
  color: white;
  font-weight: 600;
}
.chart-card {
  padding: 17px;
  margin-bottom: 16px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 6px 18px rgba(0,0,0,.06);
}
.chart-header h2 {
  margin: 0;
  font-size: 17px;
  color: #334155;
}
.chart-header p {
  margin: 5px 0 0;
  color: #94a3b8;
  font-size: 11px;
}
.chart {
  width: 100%;
  height: 280px;
  margin-top: 12px;
}
.chart-message {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}
.detail-card {
  padding: 17px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 6px 18px rgba(0,0,0,.06);
}
.detail-title {
  margin-bottom: 13px;
  font-size: 16px;
  font-weight: 600;
  color: #334155;
}
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.detail-item {
  padding: 13px;
  border-radius: 13px;
  background: #f6f8fb;
}
.detail-item span {
  display: block;
  margin-bottom: 5px;
  color: #94a3b8;
  font-size: 11px;
}
.detail-item strong {
  color: #334155;
  font-size: 14px;
}
.error {
  color: #e5484d;
}
.bottom-space {
  height: 75px;
}
</style>