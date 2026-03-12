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
  width: 200px;
  background-color: var(--sidebar-bg);
  color: var(--color-text-dark);
  height: 100vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  box-shadow: none;
}
.logo {
  padding: 20px;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  border-bottom: 1px solid var(--border-color);
  color: var(--color-text-dark);
}
nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px 0;
}
.nav-item {
  padding: 15px 20px;
  color: #666;
  text-decoration: none;
  transition: all 0.2s;
  border-radius: 12px; /* 增大圆角 */
  margin: 5px 10px;
  border: 2px solid transparent; /* 预留边框空间 */
}
.nav-item:hover {
  background-color: #f0f0f0;
  color: var(--color-text-dark);
}
.nav-item.active {
  background-color: var(--sidebar-active-bg);
  border-color: var(--sidebar-active-border); /* 边缘是 #00e2dc */
  color: var(--color-text-dark);
  font-weight: bold;
}
</style>
