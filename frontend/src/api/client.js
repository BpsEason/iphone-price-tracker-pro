import axios from 'axios';

// 💡 建立 Axios 實體
const api = axios.create({
  baseURL: '/api', 
  timeout: 10000,
});

/**
 * 🛡️ 請求攔截器
 */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

/**
 * 🛡️ 回應攔截器 - 修正跳轉無效問題
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // 💡 偵測到 401 
    if (error.response && error.response.status === 401) {
      console.warn("🔒 身份驗證失效，準備導向登入頁...");
      
      // 1. 立即清除失效 Token
      localStorage.removeItem('access_token');
      
      // 2. ✅ 使用動態導入並等待 router 實體
      try {
        const { default: router } = await import('@/router');
        
        // 3. 檢查目前是否已在登入頁，避免重複跳轉
        if (router.currentRoute.value.path !== '/login') {
          console.log("🚀 正在執行 router.push('/login')");
          
          // 使用 push 並捕捉可能的錯誤
          await router.push('/login');
        }
      } catch (routerError) {
        console.error("❌ 路由跳轉失敗，嘗試強制跳轉:", routerError);
        // 備用方案：如果 SPA 路由真的壞了，才使用強制重新整理跳轉
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// --- 🏷️ API 業務邏輯 ---
export const getProducts = () => api.get('/products');
export const triggerScrape = (target = 'All') => api.post(`/tasks/scrape?target=${target}`);
export const getMe = () => api.get('/v1/users/me');
export const getFavorites = () => api.get('/v1/favorites');
export const addFavorite = (productId) => api.post('/v1/favorites', { product_id: productId });

export default api;