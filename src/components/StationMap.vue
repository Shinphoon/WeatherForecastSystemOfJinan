<template>
  <div class="station-map">
    <div class="map-toolbar" @click.stop>
      <label>图层 <select v-model="fieldMetric" aria-label="气象插值图层"><option value="radar">雷达回波</option><option v-for="(field,key) in fieldOptions" :key="key" :value="key">{{ field.label }}</option><option value="none">仅山东省边界</option></select></label>
      <label><input v-model="showStations" type="checkbox">显示站点</label>
    </div>
    <div
      ref="mapContainer"
      class="map-container"
    ></div>
    <div v-if="fieldConfig" class="field-legend" @click.stop>
      <div class="legend-heading"><strong>{{ fieldConfig.label }}（{{ fieldConfig.unit }}）</strong><span>{{ fieldCount }} 个有效站</span></div>
      <div class="color-scale" :style="{background:fieldScale}"></div>
      <div class="scale-labels"><span v-for="stop in fieldConfig.stops" :key="stop">{{ stop }}</span></div>
      <p v-if="fieldTime">观测时次：{{ fieldTime }}</p>
      <p v-if="fieldConfig.changes">最近完整整点 − 昨天同一整点（非当前分钟值）</p>
      <p aria-live="polite">{{ fieldProgress }} · {{ fieldNotice }}</p>
    </div>
    <div class="map-attribution">边界：阿里云 DataV · 气象观测：q-weather.info · 插值仅作空间分布参考</div>
  </div>
</template>
<script setup>

import {
  ref,
  onMounted,
  onActivated,
  onBeforeUnmount,
  watch
} from 'vue'

import 'ol/ol.css'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import OSM from 'ol/source/OSM'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import XYZ from 'ol/source/XYZ'
import { useWeatherFields } from '../map/useWeatherFields'

import {
  fromLonLat,
  toLonLat
} from 'ol/proj'
import Collection from 'ol/Collection'
import Translate from 'ol/interaction/Translate'

import {
  Style,
  Circle,
  Fill,
  Stroke,
  Text
} from 'ol/style'

const props = defineProps({
  stations: {
    type: Array,
    default: () => []
  },

  selectedStationId: {
    type: String,
    default: '54823'
  },

  userLocation: {
    type: Object,
    default: () => ({
      lng: null,
      lat: null
    })
  }
})

const emit = defineEmits([
  'select',
  'location-change'
])

const mapContainer = ref(null)
const showStations = ref(true)
const {metric:fieldMetric,config:fieldConfig,scale:fieldScale,progress:fieldProgress,notice:fieldNotice,count:fieldCount,time:fieldTime,options:fieldOptions,attach:attachFields} = useWeatherFields(() => map, () => radarLayer)
watch(showStations, visible => vectorLayer?.setVisible(visible))
onActivated(() => map?.updateSize())

let map = null
let vectorSource = null
let vectorLayer = null
let radarLayer = null
let userSource = null
let userLayer = null
let userFeature = null
let userFeatures = null
let translateInteraction = null

function createUserStyle() {
  return new Style({
    image: new Circle({
      radius: 10,

      fill: new Fill({
        color: '#2563eb'
      }),

      stroke: new Stroke({
        color: '#ffffff',
        width: 4
      })
    }),

    text: new Text({
      text: '我的位置',
      offsetY: -24,
      font: 'bold 13px sans-serif',

      fill: new Fill({
        color: '#2563eb'
      }),

      stroke: new Stroke({
        color: '#ffffff',
        width: 4
      })
    })
  })
}


function renderUserLocation() {
  if (!userSource) {
    return
  }
  if (props.userLocation?.lng == null || props.userLocation?.lat == null) {
    userSource.clear()
    userFeatures?.clear()
    userFeature = null
    return
  }

  const lng =
    Number(props.userLocation?.lng)

  const lat =
    Number(props.userLocation?.lat)

  if (
    !Number.isFinite(lng) ||
    !Number.isFinite(lat)
  ) {
    return
  }

  const coordinate =
    fromLonLat([
      lng,
      lat
    ])

  if (!userFeature) {
    userFeature = new Feature({
      geometry:
        new Point(coordinate),

      featureType:
        'user-location'
    })

    userFeature.setStyle(
      createUserStyle()
    )

    userSource.addFeature(
      userFeature
    )

    userFeatures.push(
      userFeature
    )

  } else {
    userFeature
      .getGeometry()
      .setCoordinates(
        coordinate
      )
  }
}

function createStyle(
  feature
) {

  const stationId =
    feature.get('stationId')

  const selected =
    stationId ===
    props.selectedStationId

  return new Style({

    image: new Circle({

      radius:
        selected ? 9 : 7,

      fill: new Fill({

        color:
          selected
            ? '#267cff'
            : '#ffffff'

      }),

      stroke: new Stroke({

        color: '#267cff',

        width: 3

      })

    }),


    text: new Text({

      text:
        feature.get(
          'name'
        ),

      offsetY: -19,

      font:
        selected
          ? 'bold 13px sans-serif'
          : '12px sans-serif',

      fill: new Fill({

        color: '#1e293b'

      }),

      stroke: new Stroke({

        color: '#ffffff',

        width: 4

      })

    })

  })

}


function renderStations() {

  if (!vectorSource) {

    return

  }


  vectorSource.clear()


  const features = []


  props.stations.forEach(
    station => {

      const lon =
        Number(station.lon)

      const lat =
        Number(station.lat)


      if (
        Number.isNaN(lon) ||
        Number.isNaN(lat)
      ) {

        return

      }


      const feature =
        new Feature({

          geometry:
            new Point(
              fromLonLat([
                lon,
                lat
              ])
            ),

          stationId:
            station.station,

          name:
            station.name

        })


      features.push(feature)

    }
  )


  vectorSource.addFeatures(
    features
  )


  vectorLayer.changed()


  // 自动缩放到济南六个站范围
  if (
    map &&
    features.length > 1
  ) {

    map.getView().fit(

      vectorSource.getExtent(),

      {

        padding: [
          45,
          45,
          45,
          45
        ],

        maxZoom: 10,

        duration: 300

      }

    )

  }

}

async function loadRadarLayer() {

  try {

    const response = await fetch(
      'https://api.rainviewer.com/public/weather-maps.json'
    )

    if (!response.ok) {
      throw new Error(
        `RainViewer请求失败：${response.status}`
      )
    }

    const data =
      await response.json()

    const frames =
      data?.radar?.past || []

    if (frames.length === 0) {

      console.warn(
        'RainViewer暂时没有可用雷达帧'
      )

      return
    }

    // 取最新一帧
    const latestFrame =
      frames[frames.length - 1]

    const radarUrl =
      `${data.host}` +
      `${latestFrame.path}` +
      `/256/{z}/{x}/{y}/2/1_1.png`

    console.log(
      'RainViewer最新雷达：',
      new Date(
        latestFrame.time * 1000
      ).toLocaleString()
    )

    console.log(
      '雷达瓦片地址：',
      radarUrl
    )

    radarLayer =
      new TileLayer({
        visible: fieldMetric.value === 'radar',

        source:
          new XYZ({
            url: radarUrl,

            // RainViewer官方最大缩放级别为7
            maxZoom: 7,

            crossOrigin: 'anonymous'
          }),

        opacity: 0.65,

        // 确保在OSM之上
        zIndex: 5

      })

    map.addLayer(
      radarLayer
    )

  } catch (error) {

    console.error(
      'RainViewer雷达图层加载失败：',
      error
    )

  }

}

onMounted(() => {
  userSource = new VectorSource()
  userFeatures = new Collection()

  userLayer = new VectorLayer({
      source: userSource,
      zIndex: 20
    })

  vectorSource = new VectorSource()
  vectorLayer = new VectorLayer({
    source: vectorSource,
    style: createStyle,
    visible: showStations.value,
    zIndex: 10
  })

  const osmLayer = new TileLayer({
    source: new OSM(),
    zIndex: 0
  })

  map = new Map({
    target: mapContainer.value,
    layers: [
      osmLayer,
      vectorLayer,
      userLayer
    ],
    view: new View({
      center: fromLonLat([
        117.05,
        36.60
      ]),
      zoom: 9
    })
  })

  translateInteraction =
    new Translate({
      features:
        userFeatures
    })

  map.addInteraction(
    translateInteraction
  )

  translateInteraction.on(
    'translateend',
    () => {

      if (!userFeature) {
        return
      }

      const coordinate =
        userFeature
          .getGeometry()
          .getCoordinates()

      const [
        lng,
        lat
      ] = toLonLat(
        coordinate
      )

      emit(
        'location-change',
        {
          lng,
          lat
        }
      )
    }
  )

  renderUserLocation()

  renderStations()
  attachFields()

  // 加载 RainViewer 最新雷达
  loadRadarLayer()

  // 点击气象站
  map.on('singleclick', event => {
    const feature = map.forEachFeatureAtPixel(
      event.pixel,
      item => item
    )

    if (!feature) {
      return
    }

    const stationId = feature.get('stationId')

    const station = props.stations.find(
      item => item.station === stationId
    )

    if (station) {
      emit('select', station)
    }
  })

  // 鼠标移动到气象站上时变成手型
  map.on('pointermove', event => {
    const hit = map.hasFeatureAtPixel(
      event.pixel
    )

    map.getTargetElement().style.cursor =
      hit ? 'pointer' : ''
  })
})

watch(
  () => props.stations,
  () => {
    renderStations()
  },
  {
    deep: true
  }
)


watch(
  () =>
    props.selectedStationId,
  () => {
    if (vectorLayer) {
      vectorLayer.changed()
    }
  }
)

watch(
  () => props.userLocation,
  () => {
    renderUserLocation()
  },
  {
    deep: true
  }
)

onBeforeUnmount(() => {

  if (map) {

    map.setTarget(
      undefined
    )

    map = null

  }

})

</script>


<style scoped>
.map-toolbar { display:flex; justify-content:space-between; flex-wrap:wrap; align-items:center; gap:8px; padding:10px; background:#f8faff; color:#334155; font-size:12px; }
.map-toolbar label { display:flex; gap:5px; align-items:center; }
.map-toolbar select { max-width:180px; padding:7px; border:1px solid #dbe5f5; border-radius:8px; color:#334155; background:white; }
.field-legend { padding:12px; background:#fff; color:#64748b; font-size:11px; }
.legend-heading { display:flex; justify-content:space-between; gap:8px; margin-bottom:8px; }
.color-scale { height:12px; border-radius:5px; }
.scale-labels { display:flex; justify-content:space-between; margin:4px 0 8px; }
.field-legend p { margin:4px 0; line-height:1.6; }
.map-attribution { font-size:10px; color:#94a3b8; background:white; padding:4px 10px 9px; }
.station-toggle { position:absolute; right:10px; top:10px; z-index:30; display:flex; align-items:center; gap:6px; background:#fffffff0; border-radius:10px; padding:9px 12px; color:#334155; font-size:13px; box-shadow:0 2px 8px #0002; cursor:pointer; }

.station-map {
  position: relative;

  width: 100%;

  overflow: hidden;

  border-radius: 20px;

}


.map-container {

  width: 100%;

  height: 360px;

}

</style>
