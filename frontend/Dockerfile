# 階段 1: 編譯 (Build Stage)
FROM node:18-alpine AS build-stage
WORKDIR /app

# 先複製 package.json 以利用 Docker Layer Cache 縮短 build time
COPY package*.json ./
# 💡 安裝依賴，frozen-lockfile 確保版本一致性
RUN npm install --frozen-lockfile

# 複製所有原始碼並執行 Vite 編譯
COPY . .
RUN npm run build

# 階段 2: Nginx 運行 (Production Stage)
FROM nginx:stable-alpine AS production-stage
WORKDIR /usr/share/nginx/html

# 💡 從編譯階段將產出的靜態檔案 (dist) 複製過來
COPY --from=build-stage /app/dist .

# 💡 注入自定義 Nginx 配置 (這一步最關鍵，決定了 /api 能否通往後端)
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# 建立健康檢查機制
HEALTHCHECK --interval=15s --timeout=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1 

CMD ["nginx", "-g", "daemon off;"]