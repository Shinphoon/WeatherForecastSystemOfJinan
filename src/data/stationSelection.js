import { ref, watch } from 'vue'
export const selectedStationId = ref(localStorage.getItem('selectedStationId') || '54823')
watch(selectedStationId, id => localStorage.setItem('selectedStationId', String(id)))
export const productCities = new Set(['济南市', '淄博市', '泰安市', '滨州市'])
