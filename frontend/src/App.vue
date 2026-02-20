<template>
  <div id="app">
    <Navbar />
    <router-view />
    <footer class="site-footer">
      <div class="container-xl">
        <div class="footer-inner">
          <div class="footer-brand">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="rgba(255,255,255,0.7)" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="rgba(255,255,255,0.7)" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="rgba(255,255,255,0.7)" stroke-width="2" stroke-linejoin="round"/>
            </svg>
            <span class="fw-semibold">WikiSTAR</span>
          </div>
          <p class="footer-tagline">A platform for managing Wikipedia edit-a-thons</p>
          <div class="footer-links">
            <a href="https://meta.wikimedia.org" target="_blank" rel="noopener">Wikimedia</a>
            <span class="divider">·</span>
            <a href="https://en.wikipedia.org/wiki/Wikipedia:Meetup" target="_blank" rel="noopener">Wikipedia Meetups</a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>

<style>
/* Global reset & body */
*, *::before, *::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  background-color: #f8f9fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  color: #212529;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

router-view {
  flex: 1;
}

/* Footer */
.site-footer {
  background: #1a1a2e;
  color: rgba(255, 255, 255, 0.6);
  padding: 2rem 0;
  margin-top: auto;
}

.footer-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255,255,255,0.9);
  font-size: 1rem;
}

.footer-tagline {
  font-size: 0.82rem;
  margin: 0;
  color: rgba(255,255,255,0.45);
}

.footer-links {
  font-size: 0.8rem;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.footer-links a {
  color: rgba(255,255,255,0.55);
  text-decoration: none;
  transition: color 0.2s;
}

.footer-links a:hover {
  color: rgba(255,255,255,0.9);
}

.footer-links .divider {
  opacity: 0.3;
}
</style>