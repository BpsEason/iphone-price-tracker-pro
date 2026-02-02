import axios from 'axios';

const api = axios.create({
  // 根據你的 FastAPI root_path 設定，通常開發環境會透過 Vite Proxy 處理
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
});

// 💡 請求攔截器：發送請求前自動加入 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// 💡 回應攔截器：統一處理錯誤（例如 401 Token 失效）
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      // 使用原生跳轉或 Vue Router 跳轉
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;