import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path' // 💡 引入路徑工具

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // 💡 設定 @ 符號指向 src 目錄，方便你在 import 時寫 @/api/client
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // 💡 開發伺服器配置
    port: 5173,
    proxy: {
      // 💡 當你在前端呼叫 /api 時，Vite 會幫你轉發到後端伺服器
      '/api': {
        target: 'http://localhost:8888', // 👈 這裡填入你 FastAPI 後端的實際位址
        changeOrigin: true,
        // 如果後端路徑本身就有 /api，就不需要 rewrite
        // rewrite: (path) => path.replace(/^\/api/, '') 
      },
    },
  },
})