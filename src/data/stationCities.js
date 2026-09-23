import cityStations from './station-cities.json' with { type: 'json' }

// Use the supplied station table even when an older API returns missing or
// incorrect city metadata. The Python API reads this same dataset.
export const stationCityById = Object.fromEntries(
  Object.entries(cityStations).flatMap(([city, ids]) => ids.map(id => [id, city]))
)

export function normalizeStation(station) {
  const id = String(station.station ?? station.id ?? '').trim()
  const city = station.city?.trim()
  return {
    id,
    name: station.name,
    city: stationCityById[id] || (city && !['未知', '其他', '未设置', '其他站点'].includes(city) ? city : '其他站点')
  }
}
