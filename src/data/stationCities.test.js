import assert from 'node:assert/strict'
import test from 'node:test'
import groups from './station-cities.json' with { type: 'json' }
import { normalizeStation } from './stationCities.js'

test('all 146 station IDs belong to exactly one of 16 cities', () => {
  const ids = Object.values(groups).flat()
  assert.equal(Object.keys(groups).length, 16)
  assert.equal(ids.length, 146)
  assert.equal(new Set(ids).size, ids.length)
  for (const [city, stations] of Object.entries(groups)) {
    for (const station of stations) {
      for (const staleCity of [undefined, '未知', '其他站点', '错误城市']) {
        assert.equal(normalizeStation({ station, city: staleCity }).city, city)
      }
    }
  }
})

test('Zibo includes all eight stations, including Linzi, regardless of stale city data', () => {
  assert.deepEqual(groups['淄博市'], ['54729', '54824', '54825', '54829', '54830', '54833', '54834', '54836'])
  assert.equal(normalizeStation({ station: '54834', name: '临淄', city: '潍坊市' }).city, '淄博市')
  assert.ok(!groups['潍坊市'].includes('54834'))
})

test('numeric and padded IDs normalize; genuinely new stations retain city metadata', () => {
  assert.equal(normalizeStation({ id: 54833 }).city, '淄博市')
  assert.equal(normalizeStation({ station: ' 54825 ' }).city, '淄博市')
  assert.equal(normalizeStation({ station: '99999', city: '济南市' }).city, '济南市')
  assert.equal(normalizeStation({ station: '99999', city: '未知' }).city, '其他站点')
})
