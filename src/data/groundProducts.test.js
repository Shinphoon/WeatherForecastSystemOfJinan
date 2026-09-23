import test from 'node:test'
import assert from 'node:assert/strict'
import { groundCategories, buildGroundImage, groundCandidates } from './groundProducts.js'

test('provided product filenames match the supplied Beijing-time examples', () => {
  const products = groundCategories.flatMap(item => item.products)
  const hourlyEnd = Date.parse('2026-09-17T10:00:00+08:00')
  const realtimeEnd = Date.parse('2026-09-17T10:45:00+08:00')
  const starts = { 1: '20260917090000', 3: '20260917070000', 6: '20260917040000', 12: '20260916220000', 24: '20260916100000' }
  for (const product of products) {
    const result = buildGroundImage(product, product.hours ? hourlyEnd : realtimeEnd)
    const start = starts[product.hours] || '20260917104400'
    const end = product.hours ? '20260917100000' : '20260917104500'
    assert.equal(result.url, `https://jnapp.weathermate.com.cn:8009/media/data/product_img/blend/20260917/${product.prefix}_${encodeURIComponent('济南市')}_${start}_${end}_${product.hours}.png`)
  }
  assert.equal(groundCategories.length, 5)
  assert.equal(products.length, 15)
})

test('midnight selects end-date folder and previous-day interval, independent of browser timezone', () => {
  const result = buildGroundImage(groundCategories[0].products[0], Date.parse('2026-09-18T00:00:00+08:00'))
  assert.ok(result.url.includes('/20260918/'))
  assert.ok(result.url.endsWith('_20260917230000_20260918000000_1.png'))
  const candidates = groundCandidates(groundCategories[0].products[0], Date.parse('2026-09-18T00:13:00+08:00'))
  assert.equal(candidates.length, 12)
  assert.equal(candidates[0].url, result.url)
  assert.ok(candidates[1].url.includes('/20260917/'))
})

import { ziboCategories, buildZiboImage } from './groundProducts.js'
test('Zibo uses all 13 supplied products and four categories', () => {
  assert.equal(ziboCategories.length,4)
  const products=ziboCategories.flatMap(c=>c.products)
  assert.equal(products.length,13)
  const end=Date.parse('2026-09-18T15:00:00+08:00')
  for(const p of products) {
    const start=p.since === 8 ? '20260918080000' : p.since === 20 ? '20260917200000' : ({1:'20260918140000',6:'20260918090000',12:'20260918030000',24:'20260917150000'})[p.hours]
    assert.equal(buildZiboImage(p,end).url,`/api/weather/zibo-product/20260918/370300_${p.prefix}_${start}_20260918150000.png`)
  }
})
test('Zibo since-08/20 products roll over across the day boundary', () => {
  const wind=ziboCategories.find(c=>c.id==='wind')
  const p=wind.products.find(p=>p.since===8)
  assert.match(buildZiboImage(p,Date.parse('2026-09-18T07:00:00+08:00')).url,/_20260917080000_20260918070000.png$/)
  assert.match(buildZiboImage(p,Date.parse('2026-09-18T08:00:00+08:00')).url,/_20260917080000_20260918080000.png$/)
})
