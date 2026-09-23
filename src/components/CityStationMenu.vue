<template>
  <div class="city-menu" @click.stop>
    <label>先选地级市<select v-model="city"><option v-for="item in cities" :key="item">{{ item }}</option></select></label>
    <p>再选国家站 · {{ filtered.length }} 个站点</p>
    <div class="station-list"><button v-for="station in filtered" :key="station.id" :class="{ active: station.id === selectedId }" @click="$emit('select', station)">{{ station.name }} <span>{{ station.id }}</span></button></div>
  </div>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
const props = defineProps({ stations: Array, selectedId: String })
defineEmits(['select'])
const city = ref('')
const cities = computed(() => [...new Set(props.stations.map(s => s.city))].sort((a,b) => a.localeCompare(b,'zh-CN')))
const filtered = computed(() => props.stations.filter(s => s.city === city.value))
watch(() => [props.selectedId, props.stations], () => { city.value = props.stations.find(s => s.id === props.selectedId)?.city || cities.value[0] || '' }, { immediate: true })
</script>
<style scoped>
.city-menu { position:absolute; z-index:1001; right:0; top:100%; width:min(270px,calc(100vw - 48px)); padding:12px; box-sizing:border-box; border-radius:16px; background:white; box-shadow:0 8px 25px #0002; color:#64748b; font-size:12px; }
select { display:block; width:100%; padding:10px; margin-top:8px; border:1px solid #dbe5ff; border-radius:9px; background:#f5f8ff; color:#334155; }
.station-list { max-height: min(320px,45dvh); overflow:auto; }
button { display:flex; justify-content:space-between; gap:12px; width:100%; border:0; border-radius:9px; padding:10px; background:white; text-align:left; cursor:pointer; }
button.active { background:#edf3ff; color:#4f7cff; } span { color:#94a3b8; }
</style>
