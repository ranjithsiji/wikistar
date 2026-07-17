import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Codex design tokens (Wikimedia colours, spacing, typography) as CSS
// custom properties consumed by the Codex component styles.
import '@wikimedia/codex-design-tokens/dist/theme-wikimedia-ui.css'
import '@wikimedia/codex/dist/codex.style.css'
import './assets/codex-dark.css'
import App from './App.vue'
import router from './router'
import './assets/styles.css'

createApp(App).use(createPinia()).use(router).mount('#app')
