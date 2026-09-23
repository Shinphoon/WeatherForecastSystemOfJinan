<template><div class="feedback-page"><router-link to="/mine">‹ 返回我的</router-link><FeedbackPanel /></div></template>
<script setup>
import FeedbackPanel from '../components/FeedbackPanel.vue'
</script>
<style scoped>.feedback-page { min-height:100vh; background:#f3f7fc; padding:24px 16px 90px; } a { display:inline-block; margin-bottom:18px; color:#3977e7; text-decoration:none; }</style>
