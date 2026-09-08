<template>
  <div class="radar-card">
    <!-- 地图 -->
    <div class="map-wrapper">
    <div ref="mapContainer" class="radar-map"></div>

    <div class="layer-control">
        <div class="layer-title">图层</div>

        <label>
        <input
            v-model="radarVisible"
            type="checkbox"
            @change="toggleRadar"
        />
        雷达回波
        </label>

        <label>
        <input
            v-model="boundaryVisible"
            type="checkbox"
            @change="toggleBoundary"
        />
        济南行政边界
        </label>
    </div>
    </div>

    <!-- 当前雷达时间 -->
    <div class="radar-info">
      <div>
        <span class="status-dot"></span>
        雷达回波
      </div>
      <div class="radar-time">
        {{ currentTimeText }}
      </div>
    </div>

    <!-- 时间轴 -->
    <div v-if="radarFrames.length > 0" class="timeline">
      <input
        v-model.number="currentFrameIndex"
        type="range"
        :min="0"
        :max="radarFrames.length - 1"
        step="1"
        @input="showCurrentFrame"
      />

      <div class="timeline-labels">
        <span>{{ firstTimeText }}</span>
        <span>过去约2小时</span>
        <span>{{ lastTimeText }}</span>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div class="radar-controls">
      <button
        :disabled="radarFrames.length === 0"
        @click="previousFrame"
      >
        ◀ 上一帧
      </button>

      <button
        class="play-button"
        :disabled="radarFrames.length === 0"
        @click="togglePlay"
      >
        {{ isPlaying ? '⏸ 暂停' : '▶ 播放' }}
      </button>

      <button
        :disabled="radarFrames.length === 0"
        @click="nextFrame"
      >
        下一帧 ▶
      </button>
    </div>

    <!-- 透明度 -->
    <div class="opacity-control">
      <span>雷达透明度</span>
      <input
        v-model.number="radarOpacity"
        type="range"
        min="0"
        max="1"
        step="0.05"
        @input="updateOpacity"
      />
      <span>{{ Math.round(radarOpacity * 100) }}%</span>
    </div>

    <!-- 状态 -->
    <div v-if="loading" class="message">
      正在获取雷达数据...
    </div>

    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>

    <!-- 数据来源 -->
    <div class="source">
      Radar data © RainViewer · Map © OpenStreetMap contributors
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import OSM from 'ol/source/OSM'
import XYZ from 'ol/source/XYZ'
import { fromLonLat } from 'ol/proj'
import 'ol/ol.css'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { Style, Stroke, Fill } from 'ol/style'

const mapContainer = ref(null)
const radarFrames = ref([])
const currentFrameIndex = ref(0)
const isPlaying = ref(false)
const loading = ref(true)
const errorMessage = ref('')
const radarOpacity = ref(0.65)
const radarVisible = ref(true)
const boundaryVisible = ref(true)

let map = null
let radarLayer = null
let preloadLayer = null
let boundaryLayer = null
let playTimer = null
let rainViewerHost = ''

const currentFrame = computed(() => {
  if (radarFrames.value.length === 0) return null
  return radarFrames.value[currentFrameIndex.value]
})

function formatRadarTime(timestamp) {
  if (!timestamp) return '--:--'

  return new Date(timestamp * 1000).toLocaleTimeString(
    'zh-CN',
    {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }
  )
}

const currentTimeText = computed(() => {
  if (loading.value) return '加载中...'
  if (!currentFrame.value) return '--:--'
  return `雷达时间 ${formatRadarTime(currentFrame.value.time)}`
})

const firstTimeText = computed(() => {
  if (radarFrames.value.length === 0) return '--:--'
  return formatRadarTime(radarFrames.value[0].time)
})

const lastTimeText = computed(() => {
  if (radarFrames.value.length === 0) return '--:--'
  const last = radarFrames.value[radarFrames.value.length - 1]
  return formatRadarTime(last.time)
})

function createRadarUrl(frame) {
  return (
    `${rainViewerHost}` +
    `${frame.path}` +
    `/256/{z}/{x}/{y}/2/1_1.png`
  )
}

function createRadarSource(frame) {
  return new XYZ({
    url: createRadarUrl(frame),
    maxZoom: 7,
    crossOrigin: 'anonymous',
    transition: 0
  })
}

function preloadNextFrame() {
  if (!preloadLayer || radarFrames.value.length === 0) return

  let nextIndex = currentFrameIndex.value + 1
  if (nextIndex >= radarFrames.value.length) {
    nextIndex = 0
  }

  const nextFrame = radarFrames.value[nextIndex]
  preloadLayer.setSource(
    createRadarSource(nextFrame)
  )
}

function showCurrentFrame() {
  if (!radarLayer || !currentFrame.value) return

  radarLayer.setSource(
    createRadarSource(currentFrame.value)
  )

  preloadNextFrame()
}

function previousFrame() {
  if (radarFrames.value.length === 0) return

  if (currentFrameIndex.value > 0) {
    currentFrameIndex.value--
  } else {
    currentFrameIndex.value = radarFrames.value.length - 1
  }

  showCurrentFrame()
}

function nextFrame() {
  if (radarFrames.value.length === 0) return

  if (
    currentFrameIndex.value <
    radarFrames.value.length - 1
  ) {
    currentFrameIndex.value++
  } else {
    currentFrameIndex.value = 0
  }

  showCurrentFrame()
}

function startPlay() {
  if (radarFrames.value.length === 0) return

  stopPlay()
  isPlaying.value = true

  playTimer = setInterval(() => {
    nextFrame()
  }, 1000)
}

function stopPlay() {
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }

  isPlaying.value = false
}

function togglePlay() {
  if (isPlaying.value) {
    stopPlay()
  } else {
    startPlay()
  }
}

function updateOpacity() {
  if (radarLayer) {
    radarLayer.setOpacity(radarOpacity.value)
  }
}

function toggleRadar() {
  if (radarLayer) {
    radarLayer.setVisible(radarVisible.value)
  }
}

function toggleBoundary() {
  if (boundaryLayer) {
    boundaryLayer.setVisible(boundaryVisible.value)
  }
}

function createBoundaryLayer() {
  boundaryLayer = new VectorLayer({
    source: new VectorSource({
      url: 'https://geo.datav.aliyun.com/areas_v3/bound/370100_full.json',
      format: new GeoJSON()
    }),
    style: new Style({
      stroke: new Stroke({
        color: '#2563eb',
        width: 2
      }),
      fill: new Fill({
        color: 'rgba(37, 99, 235, 0.04)'
      })
    }),
    visible: boundaryVisible.value,
    zIndex: 8
  })

  return boundaryLayer
}

async function loadRadarData() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      'https://api.rainviewer.com/public/weather-maps.json'
    )

    if (!response.ok) {
      throw new Error(
        `RainViewer请求失败：${response.status}`
      )
    }

    const data = await response.json()

    if (
      !data.radar ||
      !data.radar.past ||
      data.radar.past.length === 0
    ) {
      throw new Error('暂时没有可用的雷达数据')
    }

    rainViewerHost = data.host
    radarFrames.value = data.radar.past

    // 默认直接显示最新一帧
    currentFrameIndex.value =
      radarFrames.value.length - 1

    showCurrentFrame()

    console.log(
      'RainViewer雷达帧数量：',
      radarFrames.value.length
    )

    console.log(
      '最新雷达时间：',
      new Date(
        currentFrame.value.time * 1000
      ).toLocaleString()
    )
  } catch (error) {
    console.error(
      '雷达数据加载失败：',
      error
    )

    errorMessage.value =
      '雷达数据加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const osmLayer = new TileLayer({
    source: new OSM(),
    zIndex: 0
  })

  preloadLayer = new TileLayer({
    opacity: 0,
    zIndex: 4
  })

  radarLayer = new TileLayer({
    opacity: radarOpacity.value,
    visible: radarVisible.value,
    zIndex: 5
  })

  createBoundaryLayer()

  map = new Map({
    target: mapContainer.value,
    layers: [
      osmLayer,
      preloadLayer,
      radarLayer,
      boundaryLayer
    ],
    view: new View({
      center: fromLonLat([
        117.05,
        36.60
      ]),
      zoom: 7.5,
      minZoom: 4,
      maxZoom: 12
    })
  })

  loadRadarData()
})

onBeforeUnmount(() => {
  stopPlay()

  if (map) {
    map.setTarget(undefined)
    map = null
  }
})
</script>

<style scoped>
.radar-card {
  padding: 12px;
  border-radius: 22px;
  background: white;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
}

.radar-map {
  width: 100%;
  height: 500px;
  border-radius: 18px;
  overflow: hidden;
  background: #eef2f7;
}

.radar-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding: 0 3px;
  font-size: 13px;
  color: #475569;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 5px;
  border-radius: 50%;
  background: #22c55e;
}

.radar-time {
  font-weight: 600;
  color: #3b82f6;
}

.timeline {
  margin-top: 15px;
}

.timeline input {
  width: 100%;
  cursor: pointer;
}

.timeline-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 3px;
  font-size: 10px;
  color: #94a3b8;
}

.radar-controls {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 15px;
}

.radar-controls button {
  border: none;
  padding: 9px 11px;
  border-radius: 16px;
  background: #eef5ff;
  color: #3b82f6;
  font-size: 12px;
  cursor: pointer;
}

.radar-controls button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.radar-controls .play-button {
  padding-left: 16px;
  padding-right: 16px;
  background: #3b82f6;
  color: white;
}

.opacity-control {
  display: grid;
  grid-template-columns: auto 1fr 38px;
  align-items: center;
  gap: 10px;
  margin-top: 17px;
  padding: 11px 12px;
  border-radius: 14px;
  background: #f8fafc;
  font-size: 11px;
  color: #64748b;
}

.opacity-control input {
  width: 100%;
}

.message {
  margin-top: 12px;
  text-align: center;
  font-size: 12px;
  color: #64748b;
}

.error-message {
  margin-top: 12px;
  padding: 10px;
  border-radius: 12px;
  text-align: center;
  background: #fef2f2;
  color: #ef4444;
  font-size: 12px;
}

.source {
  margin-top: 12px;
  text-align: center;
  font-size: 9px;
  color: #94a3b8;
}

.map-wrapper {
  position: relative;
}

.layer-control {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 20;
  width: 120px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 4px 14px rgba(0,0,0,.12);
  font-size: 12px;
  color: #475569;
}

.layer-title {
  margin-bottom: 7px;
  font-weight: 700;
  color: #334155;
}

.layer-control label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 6px 0;
  cursor: pointer;
}

.layer-control input {
  cursor: pointer;
}

</style>