export const groundCategories = [
  { id: 'rain', label: '降水', products: [1, 6, 12, 24].map(hours => ({ id: `rain-${hours}`, prefix: 'total_pre', hours, label: `过去${hours}小时降水` })) },
  { id: 'temperature', label: '气温', products: [
    { id: 'temperature-now', prefix: 'tem_avg', hours: 0, label: '实时气温' },
    { id: 'temperature-max', prefix: 'tem_max', hours: 24, label: '过去24小时最高气温' },
    { id: 'temperature-min', prefix: 'tem_min', hours: 24, label: '过去24小时最低气温' }
  ] },
  { id: 'wind', label: '风', products: [1, 3, 24].map(hours => ({ id: `wind-${hours}`, prefix: 'maximum_wind_speed', hours, label: `过去${hours}小时极大风` })) },
  { id: 'visibility', label: '能见度', products: [
    { id: 'visibility-now', prefix: 'vis', hours: 0, label: '实时能见度' },
    { id: 'visibility-min', prefix: 'min_vis', hours: 24, label: '过去24小时最小能见度' }
  ] },
  { id: 'humidity', label: '相对湿度', products: [
    { id: 'humidity-now', prefix: 'rhu', hours: 0, label: '实时相对湿度' },
    { id: 'humidity-min', prefix: 'min_rhu', hours: 24, label: '过去24小时最小相对湿度' },
    { id: 'humidity-max', prefix: 'max_rhu', hours: 24, label: '过去24小时最大相对湿度' }
  ] }
]

// Shift to Beijing wall time, then use UTC methods so the browser timezone
// cannot change filenames or the date folder at midnight.
export function buildGroundImage(product, endMs) {
  const stamp = ms => new Date(ms + 8 * 3600000).toISOString().slice(0, 19).replace(/[-:T]/g, '')
  const display = ms => new Date(ms + 8 * 3600000).toISOString().slice(0, 16).replace('T', ' ')
  const startMs = endMs - (product.hours ? product.hours * 3600000 : 60000)
  const end = stamp(endMs)
  return {
    url: `https://jnapp.weathermate.com.cn:8009/media/data/product_img/blend/${end.slice(0, 8)}/${product.prefix}_${encodeURIComponent('济南市')}_${stamp(startMs)}_${end}_${product.hours}.png`,
    time: `${display(startMs)} — ${display(endMs)}（北京时间）`
  }
}

export function groundCandidates(product, now = Date.now()) {
  const step = product.hours ? 3600000 : 60000
  const latest = Math.floor(now / step) * step
  return Array.from({ length: product.hours ? 12 : 31 }, (_, i) => buildGroundImage(product, latest - i * step))
}

export const ziboCategories = [
  { id: 'rain', label: '降水', products: [1,6,12,24].map(hours => ({ id: `rain-${hours}`, prefix: 'pre', hours, label: `过去${hours}小时降水` })) },
  { id: 'temperature', label: '气温', products: [
    { id: 'temperature-now', prefix: 'tem_max', hours: 1, label: '过去1小时气温' },
    { id: 'temperature-max', prefix: 'tem_max', hours: 24, label: '过去24小时最高气温' },
    { id: 'temperature-min', prefix: 'tem_min', hours: 24, label: '过去24小时最低气温' }
  ] },
  ...['wind', 'visibility'].map(id => ({ id, label: id === 'wind' ? '风' : '能见度', products: [
    { id: `${id}-1`, prefix: id === 'wind' ? 'wind' : 'vis', hours: 1, label: id === 'wind' ? '过去1小时极大风' : '实时能见度' },
    ...[8,20].map(since => ({ id: `${id}-${since}`, prefix: id === 'wind' ? 'wind' : 'vis', since, label: `${String(since).padStart(2,'0')}时以来${id === 'wind' ? '极大风' : '最低能见度'}` }))
  ] }))
]
export function buildZiboImage(product, endMs) {
  const hour = 3600000
  let startMs = endMs - product.hours * hour
  if (product.since !== undefined) {
    startMs = Math.floor((endMs + 8 * hour) / (24 * hour)) * 24 * hour - 8 * hour + product.since * hour
    if (startMs >= endMs) startMs -= 24 * hour
  }
  const stamp = ms => new Date(ms + 8 * hour).toISOString().slice(0,19).replace(/[-:T]/g,'')
  const display = ms => new Date(ms + 8 * hour).toISOString().slice(0,16).replace('T',' ')
  const end = stamp(endMs)
  return { url: `/api/weather/zibo-product/${end.slice(0,8)}/370300_${product.prefix}_${stamp(startMs)}_${end}.png`, time: `${display(startMs)} — ${display(endMs)}（北京时间）` }
}
export function ziboCandidates(product, now = Date.now()) {
  const latest = Math.floor(now / 3600000) * 3600000
  return Array.from({length:12}, (_,i) => buildZiboImage(product,latest-i*3600000))
}
