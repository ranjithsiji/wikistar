import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/login': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/logout': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/oauth-callback': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})