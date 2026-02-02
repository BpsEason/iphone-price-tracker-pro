import { createRouter, createWebHistory } from 'vue-router';

// 1. 靜態引入首頁
import ProductList from '@/views/ProductList.vue';

// 2. 登入頁與其他頁面（使用 Lazy Loading 優化首屏加載速度）
const Login = () => import('@/views/Login.vue');
const Favorites = () => import('@/views/Favorites.vue');
const ProductHistory = () => import('@/views/ProductHistory.vue'); // 💡 新增趨勢頁面
const NotFound = () => import('@/views/NotFound.vue');

const routes = [
  { 
    path: '/', 
    name: 'Home', 
    component: ProductList 
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: Login 
  },
  { 
    path: '/favorites', 
    name: 'Favorites', 
    component: Favorites 
  },
  { 
    // 💡 價格趨勢動態路由
    // :id 是路徑參數，例如 /product/4/history
    path: '/product/:id/history', 
    name: 'ProductHistory', 
    component: ProductHistory,
    props: true // 將 URL 參數 :id 直接轉為組件內的 props
  },
  { 
    path: '/:pathMatch(.*)*', 
    name: 'NotFound', 
    component: NotFound 
  }
];

const router = createRouter({
  // 使用 Vite 環境變數設定 base path，確保部署後路徑正確
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  // 💡 換頁時自動捲動到頂部，提升使用者體驗
  scrollBehavior() {
    return { top: 0 };
  }
});

export default router;