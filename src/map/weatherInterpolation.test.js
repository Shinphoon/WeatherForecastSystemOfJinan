import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { interpolate, insidePolygons, rgbAt, weatherFields, usablePoints } from './weatherInterpolation.js'
test('IDW preserves measured values and weights nearer stations more heavily',()=>{
  const points=[{x:0,y:0,value:10},{x:100,y:0,value:20},{x:0,y:100,value:30}]
  assert.equal(interpolate(0,0,points),10)
  const v=interpolate(10,10,points)
  assert.ok(v>10&&v<20)
  assert.equal(interpolate(1000000,1000000,points),null)
  assert.equal(interpolate(20,20,points.slice(0,2)),null)
})
test('province clipping excludes ocean/outside and polygon holes',()=>{
  const geometry=JSON.parse(fs.readFileSync(new URL('../data/shandong.geojson',import.meta.url))).features[0].geometry
  assert.equal(insidePolygons(117,36.65,geometry.coordinates),true)
  assert.equal(insidePolygons(117,40,geometry.coordinates),false)
  const polygon=[[[[0,0],[10,0],[10,10],[0,10]],[[4,4],[6,4],[6,6],[4,6]]]]
  assert.equal(insidePolygons(5,5,polygon),false)
})
test('temperature endpoints and change zero use the correct colors',()=>{
  assert.deepEqual(rgbAt(-20,weatherFields.temperature),[20,43,128])
  assert.deepEqual(rgbAt(45,weatherFields.temperature),[120,0,29])
  assert.deepEqual(rgbAt(0,weatherFields.pressure_change),[247,247,247])
})
test('missing values, stale observations and different cycles are excluded; zero rain is valid',()=>{
  const now=Date.parse('2026-09-17T15:00:00+08:00')
  const row=(value,hours)=>({lon:117,lat:36,values:{rain_1h:value},times:{rain_1h:new Date(now-hours*3600000).toISOString()}})
  assert.equal(usablePoints([row(0,0),row(null,0),row(3,4),row(5,2),row(8,-1)],'rain_1h',now).length,1)
})
