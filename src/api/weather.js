import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8000'

// 获取六个气象站基本信息
export function getStations() {
  return axios.get(`${BASE_URL}/weather/stations`)
}

// 获取指定站实时天气
export function getStationRealtimeWeather(stationId) {
  return axios.get(`${BASE_URL}/weather/station/${stationId}/realtime`)
}

// 获取指定站近24小时实况
export function getStationTodayWeather(stationId) {
  return axios.get(`${BASE_URL}/weather/station/${stationId}/today`)
}

// 保留旧的济南实况接口调用方式
export function getJinanRealtimeWeather() {
  return getStationRealtimeWeather('54823')
}

export function getJinanTodayWeather() {
  return getStationTodayWeather('54823')
}

// 获取指定站未来2小时预报
export function getForecast2h(stationId = '54823') {
  return axios.get(`${BASE_URL}/weather/forecast/2h/${stationId}`)
}

// 获取指定站未来24小时预报
export function getForecast24h(stationId = '54823') {
  return axios.get(`${BASE_URL}/weather/forecast/24h/${stationId}`)
}

// 获取指定站未来7天预报
export function getForecast7d(stationId = '54823') {
  return axios.get(`${BASE_URL}/weather/forecast/7d/${stationId}`)
}

export function getGroundImage() {
  return axios.get(
    'http://127.0.0.1:8000/weather/ground-image'
  )
}

export function getCurrentAlerts() {
  return axios.get(
    `${BASE_URL}/weather/alerts/current`
  )
}