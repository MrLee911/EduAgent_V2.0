// frontend/src/main.ts — Vue 3 应用入口（全局配置 + Router + Pinia）
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import './assets/animations.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
