<template>
  <div class="station-map">
    <div
      ref="mapContainer"
      class="map-container"
    ></div>
  </div>
</template>
<script setup>

import {
  ref,
  onMounted,
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

import {
  fromLonLat
} from 'ol/proj'

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

  }

})


const emit = defineEmits([
  'select'
])

const mapContainer = ref(null)

let map = null
let vectorSource = null
let vectorLayer = null
let radarLayer = null

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
  vectorSource = new VectorSource()

  vectorLayer = new VectorLayer({
    source: vectorSource,
    style: createStyle,
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
      vectorLayer
    ],
    view: new View({
      center: fromLonLat([
        117.05,
        36.60
      ]),
      zoom: 9
    })
  })

  renderStations()

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

.station-map {

  width: 100%;

  overflow: hidden;

  border-radius: 20px;

}


.map-container {

  width: 100%;

  height: 280px;

}

</style>