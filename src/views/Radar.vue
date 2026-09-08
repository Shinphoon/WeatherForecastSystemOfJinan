<template>
  <div class="radar-page">
    <div class="radar-header">
      <div>
        <h1>天气雷达</h1>
        <p>济南及周边雷达回波监测</p>
      </div>

      <router-link
        to="/"
        class="back-button"
      >
        返回
      </router-link>
    </div>

    <RadarMap />
  </div>
</template>

<script setup>
import RadarMap from '../components/RadarMap.vue'
</script>

<style scoped>
.radar-page {
  min-height: 100vh;
  padding: 20px 16px 100px;
  box-sizing: border-box;
  background: linear-gradient(
    180deg,
    #eaf4ff 0%,
    #f5f7fa 100%
  );
}

.radar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.radar-header h1 {
  margin: 0;
  font-size: 28px;
  color: #1e293b;
}

.radar-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #94a3b8;
}

.back-button {
  padding: 8px 13px;
  border-radius: 18px;
  background: white;
  color: #3b82f6;
  text-decoration: none;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0,0,0,.06);
}
</style>