<template>
  <div class="home-page">

    <!-- 顶部标题 -->
    <header class="top-header">
      <div>
        <h1>济南市</h1>
        <p>天气实况与预报</p>
      </div>

      <div class="station-selector">

        <button
            class="location-badge"
            @click="
            selectorOpen =
                !selectorOpen
            "
        >
            📍
            {{ selectedStation.name }}

            <span>
            ▾
            </span>
        </button>


        <div
            v-if="selectorOpen"
            class="station-menu"
        >

            <button
            v-for="station in stationOptions"
            :key="station.id"
            @click="
                selectStation(
                station
                )
            "
            >
            {{ station.name }}

            <span>
                {{ station.id }}
            </span>

            </button>

        </div>

        </div>
    </header>


    <!-- 实时天气卡片 -->
    <section class="section">
      <WeatherCard
        :station-id="selectedStationId"
        :station-name="selectedStation.name"
        />
    </section>


    <!-- 天气预警 -->
    <section class="section">
      <div class="section-title">
        <span>天气预警</span>
        <span class="more">查看更多</span>
      </div>

      <div
        v-if="alertLoading && !alertData.update_time"
        class="warning-card"
      >
        <div class="warning-icon">⚠</div>
        <div class="warning-content">
          <div class="warning-title">
            正在加载天气预警...
          </div>
        </div>
      </div>

      <div
        v-else-if="alertData.has_alert"
        class="warning-card"
        :class="warningLevelClass"
      >
        <div class="warning-icon">⚠</div>

        <div class="warning-content">
          <div class="warning-title-row">
            <div class="warning-title">
              {{ alertData.latest.title }}
            </div>

            <span
              v-if="alertData.mock"
              class="mock-badge"
            >
              模拟预警
            </span>
          </div>

          <div class="warning-desc">
            {{ alertData.latest.type }}
            {{ alertData.latest.level }}
          </div>

          <div
            v-if="alertData.latest.sender"
            class="warning-meta"
          >
            发布单位：{{ alertData.latest.sender }}
          </div>

          <div
            v-if="alertData.latest.publish_time"
            class="warning-meta"
          >
            发布时间：{{ alertData.latest.publish_time }}
          </div>

          <div
            v-if="alertData.latest.description"
            class="warning-description"
          >
            {{ alertData.latest.description }}
          </div>

          <div class="warning-time">
            当前共有 {{ alertData.count }} 条济南地区预警
          </div>
        </div>
      </div>

      <div
        v-else
        class="warning-card"
      >
        <div class="warning-icon">⚠</div>

        <div class="warning-content">
          <div class="warning-title">
            暂无生效中的气象预警
          </div>

          <div class="warning-desc">
            如有新的济南市气象预警，将在此处显示
          </div>
        </div>
      </div>
    </section>

    <!-- 过去1小时降水实况图 -->
    <section class="section">
      <div class="section-title">
        <span>过去1小时降水实况图</span>
        <router-link to="/reality" class="more">
          查看实况
        </router-link>
      </div>

      <div class="ground-image-card">
        <div
          v-if="groundImageLoading && !groundImageUrl"
          class="ground-image-loading"
        >
          正在加载降水实况图...
        </div>

        <img
          v-else-if="groundImageUrl"
          :src="groundImageUrl"
          class="ground-image"
          alt="济南市过去1小时降水实况图"
        >

        <div
          v-else
          class="ground-image-loading"
        >
          暂无过去1小时降水实况图
        </div>

        <div
          v-if="groundImageTime"
          class="ground-image-info"
        >
          <span>过去1小时累计降水</span>
          <span>统计时段：{{ groundImageTime }}</span>
        </div>
      </div>
    </section>

    <!-- WebGIS 地图入口 -->
    <section class="section">
      <div class="section-title">
        <span>天气实况地图</span>
        <router-link to="/radar" class="more">
          查看地图
        </router-link>
      </div>

      <router-link
        to="/reality"
        class="map-card"
      >
        <StationMap
          :stations="stationMapData"
          :selected-station-id="selectedStationId"
          @select="selectStation"
        />
      </router-link>
    </section>

        <!-- 拾风观象台最新推文 -->
    <section class="section">
      <div class="section-title">
        <span>拾风观象台 · 最新推文</span>

        <a
          v-if="wechatArticle"
          :href="wechatArticle.url"
          target="_blank"
          rel="noopener noreferrer"
          class="more"
        >
          阅读原文
        </a>
      </div>

      <!-- 加载骨架屏 -->
      <div
        v-if="wechatLoading"
        class="wechat-skeleton"
      >
        <div class="wechat-skeleton-cover"></div>

        <div class="wechat-skeleton-content">
          <div class="wechat-skeleton-account">
            <div class="wechat-skeleton-avatar"></div>

            <div class="wechat-skeleton-account-text">
              <div class="skeleton-line skeleton-line-short"></div>
              <div class="skeleton-line skeleton-line-mini"></div>
            </div>
          </div>

          <div class="skeleton-line skeleton-line-title"></div>
          <div class="skeleton-line skeleton-line-title second"></div>

          <div class="wechat-skeleton-footer">
            <div class="skeleton-line skeleton-line-date"></div>
            <div class="skeleton-line skeleton-line-read"></div>
          </div>
        </div>
      </div>

      <!-- 加载失败 -->
      <div
        v-else-if="wechatError"
        class="wechat-error-card"
        @click="loadWechatArticle"
      >
        <div class="wechat-error-icon">
          📭
        </div>

        <div>
          <div class="wechat-error-title">
            {{ wechatError }}
          </div>

          <div class="wechat-error-desc">
            点击重新加载
          </div>
        </div>
      </div>

      <!-- 正常文章 -->
      <a
        v-else-if="wechatArticle"
        :href="wechatArticle.url"
        target="_blank"
        rel="noopener noreferrer"
        class="wechat-card"
      >
        <div class="wechat-cover-wrap">

          <!-- 图片还没加载出来时显示渐变背景 -->
          <div
            v-if="!wechatImageLoaded || wechatImageError"
            class="wechat-cover-placeholder"
          >
            <div class="wechat-placeholder-icon">
              🌤
            </div>

            <div class="wechat-placeholder-text">
              拾风观象台
            </div>
          </div>

          <img
            v-if="!wechatImageError"
            :src="wechatArticle.cover"
            :alt="wechatArticle.title"
            class="wechat-cover"
            referrerpolicy="no-referrer"
            @load="handleWechatImageLoad"
            @error="handleWechatImageError"
          >

          <div class="wechat-cover-tag">
            最新推文
          </div>
        </div>

        <div class="wechat-content">

          <div class="wechat-account">
            <div class="wechat-logo">
              砜
            </div>

            <div class="wechat-account-info">
              <span class="wechat-account-name">
                拾风观象台
              </span>
            </div>
          </div>

          <div class="wechat-title">
            {{ wechatArticle.title }}
          </div>

          <div class="wechat-footer">
            <span>
              {{ formatWechatDate(wechatArticle.publish_time) }}
            </span>

            <span class="wechat-read">
              阅读全文 →
            </span>
          </div>

        </div>
      </a>
    </section>

    <!-- 短时天气 -->
    <section class="section">
      <div class="section-title">
        <span>短时天气</span>
        <router-link
          to="/forecast"
          class="more"
        >
          更多预报
        </router-link>
      </div>

      <div class="short-forecast-card">

        <div class="forecast-icon">
          {{ shortForecastIcon }}
        </div>

        <div class="forecast-content">

          <div class="forecast-title">
            {{ selectedStation.name }} · 未来2小时
          </div>

          <div
            v-if="shortLoading"
            class="forecast-text"
          >
            正在加载真实预报数据...
          </div>

          <div
            v-else-if="shortError"
            class="forecast-text forecast-error"
          >
            {{ shortError }}
          </div>

          <div
            v-else
            class="forecast-text"
          >
            {{ shortForecastText }}
          </div>

        </div>

      </div>
    </section>

    

    <!-- 24小时预报 -->
    <section class="section">

      <div class="section-title">
        <span>24小时天气趋势</span>

        <router-link
          to="/forecast"
          class="more"
        >
          查看详情
        </router-link>
      </div>


      <div class="hourly-card">

        <div
          v-for="item in hourlyForecast"
          :key="item.time"
          class="hour-item"
        >

          <div class="hour-time">
            {{ item.time }}
          </div>

          <div class="hour-icon">
            {{ item.icon }}
          </div>

          <div class="hour-temp">
            {{ item.temp }}℃
          </div>

        </div>

      </div>

    </section>


    <!-- 底部留白，避免被导航栏遮挡 -->
    <div class="bottom-space"></div>

  </div>
</template>

<script setup>
      import { ref, computed, watch, onMounted, onUnmounted, onActivated} from 'vue'
      import WeatherCard from '../components/WeatherCard.vue'
      import StationMap from '../components/StationMap.vue'
      import { getStations, getLatestWechatArticle, getForecast2h, getForecast24h, getGroundImage, getCurrentAlerts} from '../api/weather'

      const stationOptions = [
        { id:'54823', name:'济南' },
        { id:'54727', name:'章丘' },
        { id:'54816', name:'长清' },
        { id:'54818', name:'平阴' },
        { id:'54821', name:'济阳' },
        { id:'54828', name:'莱芜' }
      ]

      const savedStationId = localStorage.getItem('selectedStationId')
      const selectedStationId = ref(
        stationOptions.some(item => item.id === savedStationId)
          ? savedStationId
          : '54823'
      )

      const selectorOpen = ref(false)
      const stationMapData = ref([])
      const hourlyForecast = ref([])
      const shortForecastText = ref('')
      const shortForecastIcon = ref('🌤')
      const shortLoading = ref(true)
      const shortError = ref('')

      const selectedStation = computed(() => {
        return stationOptions.find(
          item => item.id === selectedStationId.value
        ) || stationOptions[0]
      })

      const groundImageUrl = ref('')
      const groundImageTime = ref('')
      const groundImageLoading = ref(false)
      let groundImageTimer = null

      const alertData = ref({
        has_alert: false,
        count: 0,
        latest: null,
        update_time: ''
      })

      const alertLoading = ref(false)
      let alertTimer = null

      const wechatArticle = ref(null)
      const wechatLoading = ref(true)
      const wechatError = ref('')

      const wechatImageLoaded = ref(false)
      const wechatImageError = ref(false)

      function handleWechatImageLoad() {
        wechatImageLoaded.value = true
      }

      function handleWechatImageError() {
        wechatImageError.value = true
      }

      async function loadWechatArticle() {
        wechatLoading.value = true
        wechatError.value = ''

        wechatImageLoaded.value = false
        wechatImageError.value = false

        try {
          const response = await getLatestWechatArticle()

          if (response.data && response.data.success) {
            wechatArticle.value = response.data
          } else {
            wechatError.value = '暂时无法获取最新推文'
          }
        } catch (err) {
          console.error('微信公众号文章加载失败：', err)
          wechatError.value = '最新推文加载失败'
        } finally {
          wechatLoading.value = false
        }
      }

      function formatWechatDate(time) {
        if (!time) return ''

        return time.slice(0, 16)
      }

      const warningLevelClass = computed(() => {
        const level = alertData.value.latest?.level

        if (level === '红色') {
          return 'warning-red'
        }

        if (level === '橙色') {
          return 'warning-orange'
        }

        if (level === '黄色') {
          return 'warning-yellow'
        }

        if (level === '蓝色') {
          return 'warning-blue'
        }

        return 'warning-active'
      })
      async function loadGroundImage() {
        groundImageLoading.value = true
        try {
          const response = await getGroundImage()
          groundImageUrl.value = `${response.data.url}?t=${Date.now()}`
          groundImageTime.value = `${response.data.start_time}—${response.data.end_time}`
        } catch (err) {
          console.error('过去1小时降水实况图加载失败：', err)
        } finally {
          groundImageLoading.value = false
        }
      }

      function selectStation(station) {
        const id = station.id || station.station
        if (!id) return
        selectedStationId.value = id
        selectorOpen.value = false
        localStorage.setItem('selectedStationId', id)
      }

      async function loadStations() {
        try {
          const response = await getStations()
          stationMapData.value = response.data
        } catch (err) {
          console.error('站点信息加载失败：', err)
        }
      }

      function getWeatherIcon(code) {
        if (code === 0) return '☀️'
        if (code === 1 || code === 2) return '🌤'
        if (code === 3) return '☁️'
        if (code === 45 || code === 48) return '🌫'
        if (code >= 51 && code <= 57) return '🌦'
        if (code >= 61 && code <= 67) return '🌧'
        if (code >= 71 && code <= 77) return '🌨'
        if (code >= 80 && code <= 82) return '🌦'
        if (code >= 85 && code <= 86) return '🌨'
        if (code >= 95 && code <= 99) return '⛈'
        return '☁️'
      }

      function formatForecastTime(time) {
        if (!time) return '--:--'
        return time.slice(11,16)
      }

      async function loadForecast2h() {
        shortLoading.value = true
        shortError.value = ''
        try {
          const response = await getForecast2h(
            selectedStationId.value
          )

          const data = response.data

          shortForecastText.value =
            data.text || '暂无未来2小时预报数据'

          if (
            data.hours &&
            data.hours.length > 0
          ) {
            shortForecastIcon.value =
              getWeatherIcon(
                data.hours[0].weather_code
              )
          }

        } catch (err) {
          console.error(
            '未来2小时预报加载失败：',
            err
          )

          shortError.value =
            '未来2小时预报加载失败'

        } finally {
          shortLoading.value = false
        }
      }

      async function loadForecast24h() {
        try {
          const response =
            await getForecast24h(
              selectedStationId.value
            )

          const data = response.data

          hourlyForecast.value =
            data
              .filter(
                (_, index) =>
                  index % 3 === 0
              )
              .slice(0,6)
              .map(item => ({
                time:
                  formatForecastTime(
                    item.time
                  ),
                icon:
                  getWeatherIcon(
                    item.weather_code
                  ),
                temp:
                  Math.round(
                    item.temperature
                  ),
                precipitationProbability:
                  item.precipitation_probability
              }))

        } catch (err) {
          console.error(
            '未来24小时预报加载失败：',
            err
          )

          hourlyForecast.value = []
        }
      }

      async function loadForecasts() {
        await Promise.all([
          loadForecast2h(),
          loadForecast24h()
        ])
      }

      watch(
        selectedStationId,
        () => {
          localStorage.setItem(
            'selectedStationId',
            selectedStationId.value
          )

          loadForecasts()
        },
        { immediate:true }
      )

      async function loadAlerts() {
      alertLoading.value = true

      try {
        const response =
          await getCurrentAlerts()

        alertData.value =
          response.data

      } catch (err) {
        console.error(
          '天气预警加载失败：',
          err
        )

      } finally {
        alertLoading.value = false
      }
    }

    onMounted(() => {
      loadStations()
      loadGroundImage()
      loadAlerts()

      groundImageTimer = setInterval(() => {
        loadGroundImage()
      }, 300000)

      alertTimer = setInterval(() => {
        loadAlerts()
      }, 60000)
    })

    onUnmounted(() => {
      if (groundImageTimer) {
        clearInterval(groundImageTimer)
      }

      if (alertTimer) {
        clearInterval(alertTimer)
      }
    })

    onActivated(() => {
      if (!wechatArticle.value) {
        loadWechatArticle()
      }
    })
</script>

<style scoped>
.home-page {
  width: 100%;
  min-height: 100vh;
  box-sizing: border-box;

  padding: 20px 16px;

  background:
    linear-gradient(
      180deg,
      #eaf4ff 0%,
      #f5f8fc 280px,
      #f5f7fa 100%
    );
}


/* =========================
   顶部
========================= */

.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 20px;
}


.top-header h1 {
  margin: 0;

  font-size: 30px;
  line-height: 1.2;

  color: #1e293b;
}


.top-header p {
  margin: 5px 0 0;

  font-size: 14px;

  color: #64748b;
}


.location-badge {
  padding: 8px 12px;

  border-radius: 18px;

  background: rgba(255, 255, 255, 0.8);

  color: #267cff;

  font-size: 13px;

  box-shadow:
    0 3px 12px rgba(0, 0, 0, 0.05);
}


/* =========================
   公共 section
========================= */

.section {
  margin-bottom: 22px;
}


.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 10px;

  font-size: 17px;
  font-weight: 600;

  color: #1f2937;
}


.more {
  text-decoration: none;

  font-size: 13px;
  font-weight: 400;

  color: #267cff;
}


/* =========================
   天气预警
========================= */

.warning-card {
  display: flex;
  align-items: center;

  padding: 16px;

  background: white;

  border-radius: 18px;

  box-shadow:
    0 5px 16px rgba(0, 0, 0, 0.06);
}


.warning-icon {
  display: flex;
  align-items: center;
  justify-content: center;

  flex-shrink: 0;

  width: 44px;
  height: 44px;

  margin-right: 12px;

  border-radius: 14px;

  background: #fff4dc;

  font-size: 23px;
}


.warning-content {
  flex: 1;
}


.warning-title {
  font-size: 15px;
  font-weight: 600;

  color: #374151;
}


.warning-desc {
  margin-top: 5px;

  font-size: 12px;
  line-height: 1.5;

  color: #94a3b8;
}


/* =========================
   地图卡片
========================= */

.map-card {
  display: block;

  text-decoration: none;

  color: inherit;
}


.map-background {
  position: relative;

  height: 220px;

  overflow: hidden;

  border-radius: 20px;

  background:
    radial-gradient(
      circle at 65% 30%,
      rgba(255,255,255,0.3),
      transparent 35%
    ),
    linear-gradient(
      135deg,
      #4d8df7,
      #2b6de0
    );

  box-shadow:
    0 7px 18px rgba(38, 124, 255, 0.18);
}


.map-background::before {
  content: "";

  position: absolute;

  left: 20px;
  right: 20px;
  top: 75px;

  height: 2px;

  transform: rotate(-9deg);

  background:
    rgba(255, 255, 255, 0.22);

  box-shadow:
    0 35px 0 rgba(255, 255, 255, 0.15),
    0 70px 0 rgba(255, 255, 255, 0.12);
}


.map-title {
  position: absolute;

  left: 18px;
  top: 18px;

  color: white;

  font-size: 18px;
  font-weight: 600;
}


.map-subtitle {
  position: absolute;

  left: 18px;
  top: 45px;

  color: rgba(255, 255, 255, 0.8);

  font-size: 12px;
}


.station-point {
  position: absolute;

  display: flex;
  align-items: center;

  padding: 4px 7px;

  border-radius: 10px;

  background: rgba(255, 255, 255, 0.92);

  color: #334155;

  font-size: 11px;

  box-shadow:
    0 3px 8px rgba(0, 0, 0, 0.12);
}


.dot {
  width: 7px;
  height: 7px;

  margin-right: 4px;

  border-radius: 50%;

  background: #267cff;
}


.point-1 {
  left: 42%;
  top: 48%;
}


.point-2 {
  right: 13%;
  top: 39%;
}


.point-3 {
  left: 20%;
  bottom: 22%;
}


.point-4 {
  left: 43%;
  top: 30%;
}


.point-5 {
  right: 18%;
  bottom: 18%;
}


/* =========================
   短时天气
========================= */

.short-forecast-card {
  display: flex;
  align-items: center;

  padding: 17px;

  border-radius: 18px;

  background: white;

  box-shadow:
    0 5px 16px rgba(0, 0, 0, 0.06);
}


.forecast-icon {
  display: flex;
  align-items: center;
  justify-content: center;

  flex-shrink: 0;

  width: 48px;
  height: 48px;

  margin-right: 13px;

  border-radius: 15px;

  background: #edf5ff;

  font-size: 26px;
}


.forecast-content {
  flex: 1;
}


.forecast-title {
  font-size: 15px;
  font-weight: 600;

  color: #334155;
}


.forecast-text {
  margin-top: 5px;

  font-size: 12px;
  line-height: 1.5;

  color: #94a3b8;
}


/* =========================
   24小时预报
========================= */

.hourly-card {
  display: flex;

  overflow-x: auto;

  gap: 10px;

  padding: 14px;

  background: white;

  border-radius: 18px;

  box-shadow:
    0 5px 16px rgba(0, 0, 0, 0.06);
}


.hourly-card::-webkit-scrollbar {
  display: none;
}


.hour-item {
  flex: 0 0 58px;

  text-align: center;

  padding: 7px 3px;

  border-radius: 13px;

  background: #f8fafc;
}


.hour-time {
  font-size: 11px;

  color: #94a3b8;
}


.hour-icon {
  margin: 8px 0;

  font-size: 23px;
}


.hour-temp {
  font-size: 14px;
  font-weight: 600;

  color: #334155;
}


.bottom-space {
  height: 70px;
}


.station-selector {
  position: relative;
}


.location-badge {
  border: none;

  cursor: pointer;

  display: flex;

  align-items: center;

  gap: 5px;

  padding: 9px 13px;

  background: white;

  border-radius: 18px;

  color: #267cff;

  box-shadow:
    0 3px 12px
    rgba(0,0,0,0.06);
}


.station-menu {

  position: absolute;

  z-index: 1000;

  right: 0;

  top: 46px;

  width: 155px;

  padding: 8px;

  background: white;

  border-radius: 16px;

  box-shadow:
    0 8px 25px
    rgba(0,0,0,0.14);

}


.station-menu button {

  width: 100%;

  border: none;

  background: transparent;

  padding: 10px;

  border-radius: 10px;

  display: flex;

  justify-content:
    space-between;

  cursor: pointer;

}


.station-menu button:hover {

  background: #f1f5ff;

}


.station-menu span {

  color: #94a3b8;

  font-size: 11px;

}

.forecast-error {
  color: #ef4444;
}

/* 过去1小时降水实况图 */
.ground-image-card {
  overflow: hidden;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 5px 16px rgba(0, 0, 0, 0.06);
}

.ground-image {
  display: block;
  width: 100%;
  height: auto;
}

.ground-image-loading {
  min-height: 190px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 14px;
}

.ground-image-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 13px;
  border-top: 1px solid #f1f5f9;
  color: #64748b;
  font-size: 11px;
}

.warning-active {
  border: 1px solid #e5e7eb;
}

.warning-blue {
  background: #eff6ff;
  border: 1px solid #93c5fd;
}

.warning-yellow {
  background: #fffbeb;
  border: 1px solid #facc15;
}

.warning-orange {
  background: #fff7ed;
  border: 1px solid #fb923c;
}

.warning-red {
  background: #fef2f2;
  border: 1px solid #f87171;
}

.warning-blue .warning-icon {
  background: #dbeafe;
}

.warning-yellow .warning-icon {
  background: #fef3c7;
}

.warning-orange .warning-icon {
  background: #ffedd5;
}

.warning-red .warning-icon {
  background: #fee2e2;
}

.warning-content {
  flex: 1;
  min-width: 0;
}

.warning-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.mock-badge {
  flex-shrink: 0;
  padding: 3px 7px;
  border-radius: 999px;
  background: #1f2937;
  color: white;
  font-size: 10px;
  font-weight: 600;
}

.warning-meta {
  margin-top: 5px;
  font-size: 11px;
  color: #64748b;
}

.warning-description {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: #475569;
}

.warning-time {
  margin-top: 7px;
  font-size: 11px;
  color: #94a3b8;
}

/* =========================
   拾风观象台最新推文
========================= */

.wechat-card {
  display: block;
  overflow: hidden;
  border-radius: 18px;
  background: white;
  text-decoration: none;
  color: inherit;
  box-shadow:
    0 6px 18px rgba(15, 23, 42, 0.07);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.wechat-card:active {
  transform: scale(0.985);
}

.wechat-cover-wrap {
  position: relative;
  width: 100%;
  height: 150px;
  overflow: hidden;
  background: #e8f1ff;
}

.wechat-cover {
  position: relative;
  z-index: 2;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.wechat-cover-placeholder {
  position: absolute;
  inset: 0;
  z-index: 1;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  background:
    radial-gradient(
      circle at 70% 25%,
      rgba(255,255,255,0.45),
      transparent 35%
    ),
    linear-gradient(
      135deg,
      #dcebff,
      #a8ceff
    );

  color: #267cff;
}

.wechat-placeholder-icon {
  font-size: 34px;
}

.wechat-placeholder-text {
  margin-top: 6px;
  font-size: 13px;
  font-weight: 600;
}

.wechat-cover-tag {
  position: absolute;
  z-index: 3;
  left: 12px;
  top: 12px;

  padding: 4px 9px;

  border-radius: 999px;

  background: rgba(38, 124, 255, 0.92);

  color: white;
  font-size: 11px;
  font-weight: 600;

  box-shadow:
    0 3px 10px rgba(38,124,255,0.25);
}

.wechat-content {
  padding: 13px 15px 14px;
}

.wechat-account {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.wechat-logo {
  display: flex;
  align-items: center;
  justify-content: center;

  flex-shrink: 0;

  width: 34px;
  height: 34px;

  margin-right: 9px;

  border-radius: 11px;

  background:
    linear-gradient(
      135deg,
      #267cff,
      #5aa7ff
    );

  color: white;
  font-size: 16px;
  font-weight: 700;

  box-shadow:
    0 4px 10px rgba(38,124,255,0.22);
}

.wechat-account-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  min-width: 0;
}

.wechat-account-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.wechat-author {
  margin-left: 5px;
  font-size: 10px;
  color: #94a3b8;

  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wechat-title {
  display: -webkit-box;

  overflow: hidden;

  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;

  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;

  color: #1e293b;
}

.wechat-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-top: 11px;

  font-size: 11px;
  color: #94a3b8;
}

.wechat-read {
  color: #267cff;
  font-size: 12px;
  font-weight: 500;
}

/* 加载失败 */

.wechat-error-card {
  display: flex;
  align-items: center;

  padding: 16px;

  border-radius: 18px;

  background: white;

  box-shadow:
    0 5px 16px rgba(0,0,0,0.06);

  cursor: pointer;
}

.wechat-error-icon {
  display: flex;
  align-items: center;
  justify-content: center;

  flex-shrink: 0;

  width: 44px;
  height: 44px;

  margin-right: 12px;

  border-radius: 14px;

  background: #edf5ff;

  font-size: 22px;
}

.wechat-error-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.wechat-error-desc {
  margin-top: 4px;
  font-size: 11px;
  color: #94a3b8;
}

/* 骨架屏 */

.wechat-skeleton {
  overflow: hidden;

  border-radius: 18px;

  background: white;

  box-shadow:
    0 6px 18px rgba(15,23,42,0.06);
}

.wechat-skeleton-cover {
  width: 100%;
  height: 150px;

  background:
    linear-gradient(
      90deg,
      #edf1f5 25%,
      #f6f8fa 37%,
      #edf1f5 63%
    );

  background-size: 400% 100%;

  animation:
    skeletonMove 1.4s ease infinite;
}

.wechat-skeleton-content {
  padding: 13px 15px 14px;
}

.wechat-skeleton-account {
  display: flex;
  align-items: center;

  margin-bottom: 12px;
}

.wechat-skeleton-avatar {
  width: 34px;
  height: 34px;

  flex-shrink: 0;

  margin-right: 9px;

  border-radius: 11px;

  background: #edf1f5;
}

.wechat-skeleton-account-text {
  flex: 1;
}

.skeleton-line {
  border-radius: 999px;

  background:
    linear-gradient(
      90deg,
      #edf1f5 25%,
      #f7f9fb 37%,
      #edf1f5 63%
    );

  background-size: 400% 100%;

  animation:
    skeletonMove 1.4s ease infinite;
}

.skeleton-line-short {
  width: 90px;
  height: 10px;
}

.skeleton-line-mini {
  width: 130px;
  height: 8px;

  margin-top: 7px;
}

.skeleton-line-title {
  width: 95%;
  height: 13px;

  margin-top: 8px;
}

.skeleton-line-title.second {
  width: 68%;
}

.wechat-skeleton-footer {
  display: flex;
  justify-content: space-between;

  margin-top: 15px;
}

.skeleton-line-date {
  width: 90px;
  height: 8px;
}

.skeleton-line-read {
  width: 65px;
  height: 8px;
}

@keyframes skeletonMove {
  0% {
    background-position: 100% 0;
  }

  100% {
    background-position: 0 0;
  }
}
</style>
