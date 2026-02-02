<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100/50 p-6 md:p-8">
    <div class="max-w-7xl mx-auto">
      <!-- Header Section -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 mb-10">
        <div>
          <h1 class="text-3xl md:text-4xl font-extrabold text-slate-800 tracking-tight">
            iPhone 價格追蹤
          </h1>
          <p class="mt-2 text-slate-500 text-lg">
            即時監控各大平台最新售價與優惠
          </p>
        </div>

        <div class="flex flex-wrap gap-3">
          <button
            @click="fetchProducts"
            :disabled="loading"
            class="px-5 py-2.5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200 active:scale-95 flex items-center gap-2 text-slate-700 font-medium"
          >
            <span v-if="loading" class="animate-spin">⟳</span>
            重新整理
          </button>

          <button
            @click="startScrape"
            :disabled="isScraping || loading"
            class="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-xl shadow-lg hover:shadow-xl hover:from-indigo-700 hover:to-indigo-800 disabled:opacity-60 transition-all duration-200 active:scale-95 flex items-center gap-2 font-medium"
          >
            <span v-if="isScraping" class="animate-spin">🌀</span>
            {{ isScraping ? '抓取中...' : '立即更新價格' }}
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-24">
        <div class="relative">
          <div class="h-16 w-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="h-8 w-8 bg-indigo-600/10 rounded-full animate-ping"></div>
          </div>
        </div>
        <p class="mt-6 text-slate-500 font-medium text-lg">正在載入最新價格資料...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="max-w-lg mx-auto text-center py-20">
        <div class="bg-white/80 backdrop-blur-sm p-8 rounded-3xl border border-red-100 shadow-xl">
          <div class="text-6xl mb-4">😓</div>
          <h2 class="text-2xl font-bold text-red-700 mb-3">載入失敗</h2>
          <p class="text-slate-600 mb-6">{{ error }}</p>
          <button
            @click="fetchProducts"
            class="bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-xl font-medium transition-all shadow-md hover:shadow-lg active:scale-95"
          >
            再試一次
          </button>
        </div>
      </div>

      <!-- Content -->
      <div v-else>
        <div v-if="products.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div
            v-for="product in products"
            :key="product.id"
            class="bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border border-slate-100/80 group flex flex-col"
          >
            <!-- 預留產品圖片區域（未來可綁定 product.image_url） -->
            <div class="h-48 bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center relative overflow-hidden">
              <span class="text-slate-400 text-sm font-medium">產品圖片載入中...</span>
              <!-- 如果有圖： <img :src="product.image_url" alt="" class="w-full h-full object-cover" /> -->
            </div>

            <div class="p-6 flex flex-col flex-grow">
              <div class="flex justify-between items-start mb-4">
                <span class="px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-semibold uppercase tracking-wide rounded-full">
                  {{ product.category || 'iPhone' }}
                </span>

                <button
                  @click.stop="onAddFavorite(product.id)"
                  class="p-2 rounded-full hover:bg-red-50 transition-colors group/fav"
                  :class="{ 'text-red-500': product.is_favorite }"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-7 w-7 transition-transform group-hover/fav:scale-110"
                    :fill="product.is_favorite ? 'currentColor' : 'none'"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                    />
                  </svg>
                </button>
              </div>

              <h3 class="text-xl font-bold text-slate-800 mb-3 line-clamp-2 group-hover:text-indigo-700 transition-colors">
                {{ product.name }}
              </h3>

              <div class="mt-auto pt-5 border-t border-slate-100 flex items-center justify-between text-sm">
                <span class="text-slate-500 font-mono">ID: {{ product.id }}</span>

                <router-link
                  :to="`/product/${product.id}/history`"
                  class="inline-flex items-center text-indigo-600 hover:text-indigo-800 font-semibold gap-1 transition-colors hover:gap-2"
                >
                  價格趨勢
                  <span>→</span>
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-24">
          <div class="text-7xl mb-6 text-slate-300">📭</div>
          <h2 class="text-2xl font-bold text-slate-700 mb-4">目前沒有產品資料</h2>
          <p class="text-slate-500 mb-8 max-w-md mx-auto">
            請點擊上方「立即更新價格」按鈕，啟動爬蟲任務來獲取最新資訊
          </p>
          <button
            @click="startScrape"
            :disabled="isScraping"
            class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-2xl font-medium shadow-lg hover:shadow-xl transition-all active:scale-95 flex items-center gap-2 mx-auto"
          >
            <span v-if="isScraping" class="animate-spin">🌀</span>
            開始抓取資料
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProducts, triggerScrape, addFavorite } from '@/api/client'

const products = ref([])
const loading = ref(true)
const error = ref(null)
const isScraping = ref(false)

const fetchProducts = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await getProducts()
    products.value = response.data || []
  } catch (err) {
    if (err.response?.status !== 401) {
      error.value = err.response?.data?.message || '伺服器暫時無法回應，請稍後再試'
    }
  } finally {
    loading.value = false
  }
}

const startScrape = async () => {
  if (isScraping.value) return
  isScraping.value = true
  try {
    await triggerScrape('All')
    alert('✅ 爬蟲任務已派發！\n約 1–2 分鐘後可點擊「重新整理」查看最新結果。')
  } catch (err) {
    if (err.response?.status !== 401) {
      alert('啟動失敗，請檢查後端服務是否正常運行。')
    }
  } finally {
    isScraping.value = false
  }
}

const onAddFavorite = async (id) => {
  try {
    await addFavorite(id)
    // 樂觀更新（可選）
    const product = products.value.find(p => p.id === id)
    if (product) product.is_favorite = !product.is_favorite
    alert('已加入收藏')
  } catch (err) {
    // 401 由攔截器處理
    console.error('加入收藏失敗', err)
  }
}

onMounted(fetchProducts)
</script>