<template>
  <div class="sidebar">
    <div class="logo">ClearNotify</div>
    <nav>
      <router-link to="/" class="nav-item" active-class="active">主页</router-link>
      <router-link to="/feature-a" class="nav-item" active-class="active">功能A</router-link>
      <router-link to="/feature-b" class="nav-item" active-class="active">功能B</router-link>
      <router-link to="/feature-c" class="nav-item" active-class="active">功能C</router-link>
      <router-link to="/profile" class="nav-item" active-class="active">我的</router-link>
    </nav>
  </div>
</template>

<style scoped>
.sidebar {
  width: 200px; /* 稍微窄一点 */
  background-color: #2c3e50;
  color: white;
  height: 100vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0; /* 防止被压缩 */
}
.logo {
  padding: 20px;
  font-size: 18px;
  font-weight: bold;
  text-align: center;
  border-bottom: 1px solid #34495e;
}
nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px 0;
}
.nav-item {
  padding: 15px 20px;
  color: #bdc3c7;
  text-decoration: none;
  transition: background 0.3s;
  border-left: 4px solid transparent;
}
.nav-item:hover {
  background-color: #34495e;
  color: white;
}
.nav-item.active {
  background-color: #34495e;
  color: white;
  border-left-color: #1abc9c;
}
</style>
