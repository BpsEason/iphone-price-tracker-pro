import { createApp } from 'vue'
import App from './App.vue'
import router from './router' 
import './style.css' // 👈 確保這行存在，樣式才會生效

const app = createApp(App)
app.use(router) // 👈 啟動路由功能
app.mount('#app')