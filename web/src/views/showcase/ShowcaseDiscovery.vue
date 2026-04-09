<template>
  <div class="sc-discovery">
    <ShowcaseHeader :transparent-top="true" top-text="light" />
    <div class="sc-discovery-body">
      <DiscoveryHome />
    </div>
  </div>
</template>

<script setup>
import ShowcaseHeader from '@/components/showcase/ShowcaseHeader.vue'
import DiscoveryHome from '@/views/DiscoveryHome.vue'
</script>

<style scoped>
.sc-discovery {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a0a09 0%, #c0392b 40%, #2980b9 100%);
}
.sc-discovery-body { padding-top: 64px; }
</style>
