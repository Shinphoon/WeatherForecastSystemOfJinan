<template>
  <section class="ground-products" @click.stop>
    <h2>{{ cityName }}实况产品</h2>
    <div class="category-tabs" aria-label="实况要素">
      <button v-for="item in categories" :key="item.id" :aria-pressed="categoryId === item.id"
        :class="{ active: categoryId === item.id }" @click="selectCategory(item)">{{ item.label }}</button>
    </div>
    <div class="product-card">
      <div class="product-controls">
        <label for="ground-type">实况类别</label>
        <select id="ground-type" v-model="productId"><option v-for="item in category.products" :key="item.id" :value="item.id">{{ item.label }}</option></select>
      </div>
      <div class="product-heading"><h3>{{ product.label }}实况图</h3><span>{{ cityName }}市</span></div>
      <div v-if="loading" class="product-state" role="status">正在查找最新{{ product.label }}实况图…</div>
      <template v-else-if="image">
        <a :href="image.url" target="_blank" rel="noopener noreferrer" title="打开原图查看"><img :src="image.url" :alt="`${cityName}市${product.label}实况图`" @error="image = null" /></a>
        <p class="product-time">{{ image.time }}</p>
        <p class="source-note">{{ cityName }}市气象台 · 点击图片查看原图</p>
      </template>
      <div v-else class="product-state" role="status">暂未获取到该产品，图片可能尚未发布或暂时无法访问。<button @click="loadImage">重新加载</button></div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch, onMounted, onActivated, onDeactivated, onBeforeUnmount } from 'vue'
import { groundCategories, groundCandidates, ziboCategories, ziboCandidates } from '../data/groundProducts'
const props = defineProps({ city: { type: String, default: 'jinan' } })
const cityName = computed(() => props.city === 'zibo' ? '淄博' : '济南')
const categories = computed(() => props.city === 'zibo' ? ziboCategories : groundCategories)
const categoryId = ref('rain')
const productId = ref('rain-1')
const category = computed(() => categories.value.find(item => item.id === categoryId.value))
const product = computed(() => category.value.products.find(item => item.id === productId.value) || category.value.products[0])
const image = ref(null)
const loading = ref(false)
const remembered = {}
let controller
let timer
function selectCategory(item) {
  remembered[categoryId.value] = productId.value
  categoryId.value = item.id
  productId.value = remembered[item.id] || item.products[0].id
}
function imageExists(url, signal) {
  return new Promise(resolve => {
    const img = new Image()
    let timeout
    const finish = result => {
      clearTimeout(timeout)
      img.onload = img.onerror = null
      signal.removeEventListener('abort', abort)
      if (!result) img.src = ''
      resolve(result)
    }
    const abort = () => finish(false)
    if (signal.aborted) { resolve(false); return }
    signal.addEventListener('abort', abort, { once: true })
    img.onload = () => finish(true)
    img.onerror = () => finish(false)
    timeout = setTimeout(() => finish(false), 4000)
    img.src = url
  })
}
async function loadImage() {
  controller?.abort()
  const request = new AbortController()
  controller = request
  loading.value = true
  image.value = null
  const candidates = (props.city === 'zibo' ? ziboCandidates : groundCandidates)(product.value)
  // Check a small group concurrently, but always prefer the newest success.
  for (let i = 0; i < candidates.length; i += 4) {
    const batch = candidates.slice(i, i + 4)
    const results = await Promise.all(batch.map(item => imageExists(item.url, request.signal)))
    if (request.signal.aborted) return
    const index = results.findIndex(Boolean)
    if (index >= 0) { image.value = batch[index]; break }
  }
  loading.value = false
}
watch(productId, loadImage)
function start() { if (timer) return; loadImage(); timer = setInterval(() => { if (!document.hidden) loadImage() }, 300000) }
onMounted(start)
onActivated(start)
function stop() { controller?.abort(); clearInterval(timer); timer = null }
onDeactivated(stop)
onBeforeUnmount(stop)
</script>

<style scoped>
.ground-products { margin-bottom: 22px; color: #243247; }
h2 { font-size: 17px; margin: 0 0 14px; }
.category-tabs { display: grid; grid-template-columns: repeat(v-bind("categories.length"), minmax(0, 1fr)); gap: 6px; margin-bottom: 12px; }
.category-tabs button { padding: 13px 2px; border: 1px solid #e1e9f4; background: white; color: #5d697d; border-radius: 13px; font: inherit; font-size: 13px; cursor: pointer; }
.category-tabs button.active { background: #388fff; color: white; border-color: #388fff; box-shadow: 0 4px 12px #388fff26; }
.product-card { background: white; border-radius: 20px; padding: 16px; box-shadow: 0 6px 24px #182f5210; }
.product-controls { display: flex; align-items: center; gap: 12px; padding-bottom: 14px; border-bottom: 1px solid #eef1f5; font-size: 13px; }
select { flex: 1; min-width: 0; padding: 10px 6px; border: 1px solid #90baff; background: #edf5ff; color: #334155; border-radius: 9px; font: inherit; }
.product-heading { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin: 16px 0; }
h3 { margin: 0; font-size: 14px; }
.product-heading span { color: #388fff; white-space: nowrap; font-size: 12px; }
img { display: block; width: 100%; height: auto; border: 1px solid #edf0f5; border-radius: 12px; box-sizing: border-box; }
.product-state { padding: 50px 12px; color: #8290a7; text-align: center; font-size: 13px; }
.product-state button { display: block; margin: 16px auto 0; border: 0; background: #edf5ff; color: #388fff; padding: 10px 16px; border-radius: 8px; cursor: pointer; }
.product-time { font-size: 11px; color: #667995; line-height: 1.7; overflow-wrap: anywhere; }
.source-note { font-size: 11px; color: #94a3b8; margin-bottom: 0; }
button:focus-visible, select:focus-visible { outline: 2px solid #388fff; outline-offset: 2px; }
</style>
