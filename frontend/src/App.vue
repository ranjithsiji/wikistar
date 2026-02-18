<template>
  <div id="app">
    <Navbar />
    <router-view />
    <footer class="app-footer">
      <span>Designed and built by <strong>Clinta C C</strong></span>
    </footer>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>

<style>
.app-footer {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 20px;
  text-align: center;
  font-size: 14px;
  margin-top: 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.app-footer strong {
  font-weight: 600;
  color: #fff;
}

.app-footer a {
  color: #fff;
  text-decoration: none;
  transition: opacity 0.3s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
}

.app-footer a:hover {
  opacity: 0.8;
  border-bottom: 1px solid rgba(255, 255, 255, 0.8);
}
</style>