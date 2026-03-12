<script setup>
import Sidebar from '@/components/common/Sidebar.vue';
import Header from '@/components/common/Header.vue';
</script>

<template>
  <div class="app-layout">
    <Sidebar />
    <div class="content-wrapper">
      <Header />
      <div class="main-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style>
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  height: 100vh;
}
.app-layout {
  display: flex;
  height: 100vh;
}
.content-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
