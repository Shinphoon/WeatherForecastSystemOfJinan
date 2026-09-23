import { computed, ref, watch, onActivated, onDeactivated, onBeforeUnmount } from 'vue'
import GeoJSON from 'ol/format/GeoJSON'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import ImageLayer from 'ol/layer/Image'
import ImageStatic from 'ol/source/ImageStatic'
import { Style, Stroke } from 'ol/style'
import boundaryText from '../data/shandong.geojson?raw'
import { weatherFields, usablePoints } from './weatherInterpolation'
import { getStationFields } from '../api/stationFields'

export function useWeatherFields(getMap, getRadar) {
  const metric=ref('temperature'), progress=ref(''), notice=ref(''), count=ref(0), time=ref('')
  const config=computed(()=>weatherFields[metric.value])
  const scale=computed(()=>{
    if(!config.value) return ''
    const {colors}=config.value
    return `linear-gradient(to right, ${colors.map((color,i)=>`${color} ${i/(colors.length-1)*100}%`).join(',')})`
  })
  let layer, worker, timer, active=false, request=0, renderId=0, lastSignature=''
  function stop() { active=false; request++; clearTimeout(timer); worker?.terminate(); worker=null; lastSignature='' }
  function render(stations,signature) {
    if(signature===lastSignature) return
    lastSignature=signature
    if(!worker) {
      worker=new Worker(new URL('./weatherField.worker.js',import.meta.url),{type:'module'})
      worker.onmessage=({data})=>{
        if(data.id!==renderId || !active || !config.value) return
        const canvas=document.createElement('canvas'); canvas.width=data.width; canvas.height=data.height
        canvas.getContext('2d').putImageData(new ImageData(data.pixels,data.width,data.height),0,0)
        layer.setSource(new ImageStatic({url:canvas.toDataURL(),imageExtent:data.extent,projection:'EPSG:3857',interpolate:true}))
      }
      worker.onerror=()=>{ notice.value='插值绘制失败，请切换图层重试'; lastSignature='' }
    }
    worker.postMessage({id:++renderId,metric:metric.value,stations})
  }
  async function refresh() {
    clearTimeout(timer)
    if(!active || !config.value) return
    if(document.hidden) { timer=setTimeout(refresh,30000); return }
    const current=++request, selected=metric.value
    let next=30000
    try {
      const {data}=await getStationFields(Boolean(config.value.changes))
      if(!active || current!==request || metric.value!==selected) return
      const stations=usablePoints(data.stations,selected)
      count.value=stations.length
      progress.value=data.loading ? `采集进度 ${data.processed}/${data.total} 站` : `已检查 ${data.total} 站 · ${data.failed} 站请求失败`
      notice.value=stations.length<3 ? '有效同周期观测不足3站，暂不绘制插值。' : '反距离加权插值（IDW），空白处为缺测或超出有效站点覆盖范围。'
      const times=stations.map(s=>Date.parse(s.times[selected])).sort((a,b)=>a-b)
      const fmt=ms=>new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(ms)
      time.value=times.length ? `${fmt(times[0])} — ${fmt(times.at(-1))}（北京时间）` : ''
      if(stations.length<3) { layer.setSource(null); renderId++ }
      else render(stations,`${selected}:${JSON.stringify(stations.map(s=>[s.id,s.values[selected],s.times[selected]]))}`)
      next=data.loading?5000:60000
    } catch {
      if(current!==request || !active) return
      layer.setSource(null); renderId++; lastSignature=''; count.value=0; time.value=''
      notice.value='观测数据暂时无法获取，请稍后重试。'; progress.value=''
    } finally {
      if(active && current===request && metric.value===selected) timer=setTimeout(refresh,next)
    }
  }
  function start() { if(active || !layer) return; active=true; refresh() }
  function attach() {
    const map=getMap()
    const boundary=new VectorLayer({source:new VectorSource({features:new GeoJSON().readFeatures(JSON.parse(boundaryText),{featureProjection:'EPSG:3857'})}),style:new Style({stroke:new Stroke({color:'#334155',width:2})}),zIndex:8})
    layer=new ImageLayer({zIndex:4})
    map.addLayer(layer); map.addLayer(boundary)
    // Keep the complete provincial outline visible on initial view.
    map.getView().fit(boundary.getSource().getExtent(),{padding:[28,28,28,28],maxZoom:8})
    start()
  }
  watch(metric,()=>{
    request++; renderId++; lastSignature=''; clearTimeout(timer)
    layer?.setSource(null); worker?.terminate(); worker=null
    count.value=0; time.value=''; notice.value=''; progress.value=''
    getRadar()?.setVisible(metric.value==='radar')
    refresh()
  })
  onActivated(start); onDeactivated(stop); onBeforeUnmount(stop)
  return { metric, config, scale, progress, notice, count, time, attach, refresh, options:weatherFields }
}
