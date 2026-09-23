export const weatherFields = {
  temperature: { label: '实时气温', unit: '℃', stops: [-20,-10,0,10,20,30,40,45], colors: ['#142b80','#215dcc','#39b7e3','#7bd6bc','#f4ed77','#f4a03b','#d63535','#78001d'] },
  humidity: { label: '实时相对湿度', unit: '%', stops: [0,20,40,60,80,100], colors: ['#a45c28','#e5ba78','#ffffca','#a1dab4','#41b6c4','#225ea8'] },
  rain_1h: { label: '实时1小时降水', unit: 'mm', stops: [0,0.1,2,5,10,20,50,100], colors: ['#f5f5f5','#b6efa0','#57bc69','#49c4e0','#3474cf','#8057cf','#da399d','#801047'] },
  rain_24h: { label: '实时24小时降水', unit: 'mm', stops: [0,0.1,10,25,50,100,250], colors: ['#f5f5f5','#b6efa0','#57bc69','#49c4e0','#3474cf','#da399d','#801047'] },
  temperature_change: { label: '24小时变温', unit: '℃', stops: [-20,-10,-5,0,5,10,20], colors: ['#142b80','#2975cb','#a6cde9','#f7f7f7','#f4b59a','#dc5843','#85001d'], changes: true },
  pressure_change: { label: '24小时变压', unit: 'hPa', stops: [-20,-10,-5,0,5,10,20], colors: ['#762a83','#af8dc3','#e7d4e8','#f7f7f7','#d9f0d3','#7fbf7b','#1b7837'], changes: true }
}
export const project = (lon, lat) => [6378137 * lon * Math.PI / 180, 6378137 * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360))]
export function insideRing(x, y, ring) {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi,yi] = ring[i], [xj,yj] = ring[j]
    if ((yi > y) !== (yj > y) && x < (xj-xi)*(y-yi)/(yj-yi)+xi) inside = !inside
  }
  return inside
}
export function insidePolygons(x,y,polygons) {
  return polygons.some(rings => insideRing(x,y,rings[0]) && !rings.slice(1).some(ring => insideRing(x,y,ring)))
}
// IDW power 2, nearest 12 stations within 150 km in projected distance.
// Require at least 3 nearby observations. Outside supported areas stays blank.
export function interpolate(x,y,points,radius=190000) {
  const nearest = []
  for (const point of points) {
    const d2 = (point.x-x)**2 + (point.y-y)**2
    if (d2 < 1) return point.value
    if (d2 <= radius*radius) nearest.push([d2,point.value])
  }
  if (nearest.length < 3) return null
  nearest.sort((a,b)=>a[0]-b[0])
  let weights = 0, values = 0
  for (const [d2,value] of nearest.slice(0,12)) { const weight=1/d2; weights+=weight; values+=weight*value }
  return values/weights
}
export function rgbAt(value, field) {
  const { stops, colors } = field
  const rgb = hex => [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16))
  if (value <= stops[0]) return rgb(colors[0])
  for (let i=1;i<stops.length;i++) if (value <= stops[i]) {
    const t=(value-stops[i-1])/(stops[i]-stops[i-1]), a=rgb(colors[i-1]), b=rgb(colors[i])
    return a.map((v,j)=>Math.round(v+(b[j]-v)*t))
  }
  return rgb(colors.at(-1))
}
export function usablePoints(stations, metric, now=Date.now()) {
  const valid=stations.filter(s=>Number.isFinite(s.values?.[metric]) && Number.isFinite(s.lon) && Number.isFinite(s.lat) && Number.isFinite(Date.parse(s.times?.[metric])) && now-Date.parse(s.times[metric])<=3*3600000 && Date.parse(s.times[metric])-now<=600000)
  const latest=Math.max(...valid.map(s=>Date.parse(s.times[metric])))
  // Avoid combining station reports more than one hour apart.
  return valid.filter(s=>latest-Date.parse(s.times[metric])<=3600000)
}
