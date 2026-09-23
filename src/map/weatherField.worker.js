import boundaryText from '../data/shandong.geojson?raw'
import { project, insidePolygons, interpolate, rgbAt, weatherFields } from './weatherInterpolation.js'
const geometry = JSON.parse(boundaryText).features[0].geometry
const coordinates = geometry.type === 'MultiPolygon' ? geometry.coordinates : [geometry.coordinates]
const polygons = coordinates.map(rings=>rings.map(ring=>ring.map(([lon,lat])=>project(lon,lat))))
const all = polygons.flat(2)
const extent = [Math.min(...all.map(p=>p[0])), Math.min(...all.map(p=>p[1])), Math.max(...all.map(p=>p[0])), Math.max(...all.map(p=>p[1]))]
const width=240, height=Math.round(width*(extent[3]-extent[1])/(extent[2]-extent[0]))
const mask=new Uint8Array(width*height)
const position = (x,y) => [extent[0]+(x+.5)/width*(extent[2]-extent[0]),extent[3]-(y+.5)/height*(extent[3]-extent[1])]
for(let y=0;y<height;y++) for(let x=0;x<width;x++) mask[y*width+x]=insidePolygons(...position(x,y),polygons)?1:0
self.onmessage = ({data}) => {
  const {id,metric,stations}=data
  const points=stations.map(s=>{const [x,y]=project(s.lon,s.lat);return {x,y,value:s.values[metric]}})
  const pixels=new Uint8ClampedArray(width*height*4)
  if (points.length>=3) for(let y=0;y<height;y++) for(let x=0;x<width;x++) {
    if(!mask[y*width+x]) continue
    const value=interpolate(...position(x,y),points)
    if(value===null) continue
    const offset=(y*width+x)*4
    pixels.set(rgbAt(value,weatherFields[metric]),offset); pixels[offset+3]=185
  }
  self.postMessage({id,width,height,extent,pixels},[pixels.buffer])
}
