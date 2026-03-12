<template>
  <div class="search-page">
    <h1>Search Results</h1>
    <p v-if="query">
      Showing results for: <strong>{{ query }}</strong>
    </p>
    <div class="placeholder">
      <!-- 这里是占位符，未来可以放搜索结果 -->
      <div v-for="i in 5" :key="i" class="result-item">
        <h3>Result {{ i }}</h3>
        <p>This is a placeholder for search result {{ i }}.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const query = computed(() => route.query.q || '');
</script>

<style scoped>
.search-page {
  padding: 20px;
}
.result-item {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 5px;
}
</style>
