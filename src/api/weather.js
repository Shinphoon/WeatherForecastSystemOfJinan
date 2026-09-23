import axios from 'axios'
import { cachedRequest } from './requestCache'
const read = (url, ttl = 60000) => cachedRequest(url, () => axios.get(url, { timeout: 20000 }), ttl)

const BASE_URL = '/api'

// 获取六个气象站基本信息
export function getStations() {
  return read(`${BASE_URL}/weather/stations`, 300000)
}

// 获取指定站实时天气
export function getStationRealtimeWeather(stationId) {
  return read(`${BASE_URL}/weather/station/${stationId}/realtime`)
}

// 获取指定站近24小时实况
export function getStationTodayWeather(stationId) {
  return read(`${BASE_URL}/weather/station/${stationId}/today`)
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
  return read(`${BASE_URL}/weather/forecast/2h/${stationId}`)
}

// 获取指定站未来24小时预报
export function getForecast24h(stationId = '54823') {
  return read(`${BASE_URL}/weather/forecast/24h/${stationId}`)
}

// 获取指定站未来7天预报
export function getForecast7d(stationId = '54823') {
  return read(`${BASE_URL}/weather/forecast/7d/${stationId}`)
}

export function getGroundImage() {
  return read(
    `${BASE_URL}/weather/ground-image`
  )
}


export function getCurrentAlerts() {
  return read(
    `${BASE_URL}/weather/alerts/current`
  )
}

export function getLatestWechatArticle() {
  return read(
    `${BASE_URL}/weather/wechat/latest`
  )
}