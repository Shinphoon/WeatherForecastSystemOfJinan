import axios from 'axios'
import { cachedRequest } from './requestCache'
export const getStationFields = changes => cachedRequest(`station-fields:${changes}`, () => axios.get('/api/weather/station-fields', {params: { changes },timeout:15000}), 4000)
