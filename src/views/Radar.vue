<template>
  <div class="radar-page">
    <div class="radar-header">
      <div>
        <h1>天气雷达</h1>
        <p>济南及周边雷达回波监测</p>
      </div>

      <router-link
        to="/"
        class="back-button"
      >
        返回
      </router-link>
    </div>

    <RadarMap
      :user-location="userLocation"
      @location-change="handleLocationChange"
    />
    <div class="echo-card">
      <div class="echo-title">
        📡 降水回波监测
      </div>

      <div v-if="radarChecking" class="echo-text">
        正在分析当前位置附近雷达回波...
      </div>

      <template v-else-if="radarStatus">

        <div
          v-if="radarStatus.status === 'raining'"
          class="echo-danger"
        >
          🌧 当前已处于降水回波影响范围
        </div>

        <div
          v-else-if="radarStatus.status === 'approaching'"
          class="echo-warning"
        >
          <div>
            🌧 降水回波正在接近
          </div>

          <div class="echo-detail">
            最近回波
            <strong>
              {{ radarStatus.distance_km }} km
            </strong>
          </div>

          <div class="echo-eta">
            预计约
            <strong>
              {{ radarStatus.eta_minutes }}
            </strong>
            分钟后可能出现降雨
          </div>

          <div class="echo-detail">
            回波接近速度约
            {{ radarStatus.speed_kmh }} km/h
          </div>
        </div>

        <div
          v-else-if="
            radarStatus.status === 'not_approaching'
          "
          class="echo-text"
        >
          附近存在降水回波，距您约
          <strong>
            {{ radarStatus.distance_km }} km
          </strong>
          ，目前暂无明显接近趋势
        </div>

        <div
          v-else-if="
            radarStatus.status === 'uncertain'
          "
          class="echo-text"
        >
          附近存在降水回波，但移动趋势暂不稳定
        </div>

        <div
          v-else
          class="echo-safe"
        >
          当前100 km范围内未检测到降水回波
        </div>

      </template>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  onMounted
} from 'vue'

import RadarMap from '../components/RadarMap.vue'

import {
  getCurrentUser,
} from '../api/auth'


const userLocation = ref({
  lng: null,
  lat: null
})

const radarStatus = ref(null)
const radarChecking = ref(false)

async function loadRadarDistance(lat, lng) {
  if (
    lat === null ||
    lat === undefined ||
    lng === null ||
    lng === undefined
  ) {
    return
  }

  radarChecking.value = true

  try {
    const response = await fetch(
      `/api/weather/radar/approach?lat=${lat}&lng=${lng}`
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.detail ||
        '雷达趋势分析失败'
      )
    }

    radarStatus.value = data

    console.log(
      '雷达趋势分析：',
      data
    )

  } catch (error) {
    console.error(
      '雷达趋势分析失败：',
      error
    )

    radarStatus.value = null

  } finally {
    radarChecking.value = false
  }
}

async function loadUserLocation() {
  try {
    const response = await getCurrentUser()

    const lng = response.data.last_lng
    const lat = response.data.last_lat

    userLocation.value = {
      lng,
      lat
    }

    console.log(
      '读取到用户位置：',
      userLocation.value
    )

    await loadRadarDistance(
      lat,
      lng
    )

  } catch (error) {
    console.error(
      '读取用户位置失败：',
      error
    )
  }
}

async function handleLocationChange(location) {
  try {
    const token =
      localStorage.getItem(
        'access_token'
      )

    const response = await fetch(
      '/api/auth/location',
      {
        method: 'PUT',

        headers: {
          'Content-Type':
            'application/json',

          Authorization:
            `Bearer ${token}`
        },

        body: JSON.stringify({
          lng: Number(location.lng),
          lat: Number(location.lat),
          alt: null
        })
      }
    )

    const data =
      await response.json()

    if (!response.ok) {
      throw new Error(
        data.detail ||
        '位置更新失败'
      )
    }

    userLocation.value = {
      lng: data.lng,
      lat: data.lat
    }

    await loadRadarDistance(
      data.lat,
      data.lng
    )

    const syncLocation = {
      lng: data.lng,
      lat: data.lat,
      alt: data.alt ?? null,
      address: data.address || '',
      nearestStation:
        data.nearest_station || null
    }

    localStorage.setItem(
      'syncedUserLocation',
      JSON.stringify(syncLocation)
    )

    if (data.nearest_station) {
      localStorage.setItem(
        'selectedStationId',
        data.nearest_station.id
      )
    }

    console.log(
      '雷达位置保存成功：',
      data
    )

  } catch (error) {
    console.error(
      '更新雷达定位失败：',
      error
    )
  }
}

onMounted(() => {
  loadUserLocation()
})
</script>

<style scoped>
.radar-page {
  min-height: 100vh;
  padding: 20px 16px 100px;
  box-sizing: border-box;
  background: linear-gradient(
    180deg,
    #eaf4ff 0%,
    #f5f7fa 100%
  );
}

.radar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.radar-header h1 {
  margin: 0;
  font-size: 28px;
  color: #1e293b;
}

.radar-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #94a3b8;
}

.back-button {
  padding: 8px 13px;
  border-radius: 18px;
  background: white;
  color: #3b82f6;
  text-decoration: none;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0,0,0,.06);
}

.echo-card {
  margin-top: 14px;
  padding: 16px;
  border-radius: 18px;
  background: white;
  box-shadow: 0 6px 18px rgba(15, 23, 42, .06);
}

.echo-title {
  margin-bottom: 10px;
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}

.echo-text {
  font-size: 13px;
  color: #475569;
}

.echo-text strong {
  font-size: 20px;
  color: #2563eb;
}

.echo-danger {
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff1f2;
  color: #e11d48;
  font-size: 13px;
  font-weight: 600;
}

.echo-safe {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f0fdf4;
  color: #16a34a;
  font-size: 13px;
}

.echo-warning {
  padding: 12px;
  border-radius: 12px;
  background: #fff7ed;
  color: #c2410c;
  font-size: 13px;
  font-weight: 600;
}

.echo-detail {
  margin-top: 8px;
  font-weight: 400;
  color: #64748b;
}

.echo-eta {
  margin-top: 8px;
  font-size: 15px;
  color: #ea580c;
}

.echo-eta strong {
  font-size: 22px;
}
</style>