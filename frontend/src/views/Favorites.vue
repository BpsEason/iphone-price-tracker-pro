<template>
  <div class="min-h-screen bg-stone-50/70 p-4 sm:p-6 md:p-8 font-sans text-zinc-800">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <header class="mb-10 md:mb-14 flex flex-col sm:flex-row sm:items-center justify-between gap-5">
        <div class="flex items-center gap-3">
          <div class="text-4xl sm:text-5xl">❤️</div>
          <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-zinc-900">
            我的收藏清單
          </h1>
        </div>

        <router-link
          to="/"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-stone-200 rounded-full text-zinc-700 font-medium shadow-sm hover:shadow-md hover:border-orange-300 hover:text-orange-700 transition-all duration-200 group"
        >
          <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回探索
        </router-link>
      </header>

      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-32">
        <div class="relative">
          <div class="h-14 w-14 border-4 border-amber-100 border-t-amber-600 rounded-full animate-spin"></div>
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="h-6 w-6 bg-amber-600/10 rounded-full animate-ping"></div>
          </div>
        </div>
        <p class="mt-6 text-zinc-500 font-medium">正在載入您的珍藏...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="favorites.length === 0" class="bg-white/80 backdrop-blur-sm border-2 border-dashed border-stone-300/70 rounded-3xl p-12 md:p-20 text-center shadow-inner">
        <div class="text-7xl md:text-8xl mb-6 opacity-80">🏜️</div>
        <h2 class="text-2xl md:text-3xl font-bold text-zinc-400 mb-4">收藏清單目前是空的</h2>
        <p class="text-zinc-500 max-w-md mx-auto mb-10">
          尋找能點燃您「午火」能量的優質好物，加入這裡吧
        </p>
        <router-link
          to="/"
          class="inline-flex items-center px-8 py-4 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-bold rounded-2xl shadow-lg hover:shadow-xl hover:from-orange-700 hover:to-amber-700 transition-all duration-300 active:scale-95"
        >
          立即探索好物
        </router-link>
      </div>

      <!-- Favorites Grid -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 md:gap-8">
        <div
          v-for="item in favorites"
          :key="item.id"
          class="group bg-white rounded-3xl overflow-hidden shadow-md hover:shadow-2xl hover:-translate-y-2 transition-all duration-400 border border-stone-100/80 flex flex-col"
        >
          <!-- 圖片區域（未來可綁定 item.product_image_url） -->
          <div class="relative h-52 sm:h-56 bg-gradient-to-br from-stone-100 to-amber-50 overflow-hidden">
            <div v-if="!item.product_image_url" class="absolute inset-0 flex items-center justify-center">
              <span class="text-stone-400 text-sm font-medium">產品圖片</span>
            </div>
            <img
              v-else
              :src="item.product_image_url"
              :alt="item.product_name"
              class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <!-- 平台標籤浮在圖片上 -->
            <span class="absolute top-4 left-4 px-3 py-1 bg-white/90 backdrop-blur-sm text-amber-800 text-xs font-bold uppercase tracking-wide rounded-full shadow-sm border border-amber-100/50">
              {{ item.platform_name || '平台' }}
            </span>
          </div>

          <div class="p-6 flex flex-col flex-grow">
            <!-- 商品名稱 -->
            <h3 class="font-bold text-lg leading-tight text-zinc-900 mb-4 line-clamp-2 min-h-[2.75rem] group-hover:text-orange-700 transition-colors">
              {{ item.product_name }}
            </h3>

            <!-- 價格 -->
            <div class="mt-auto mb-6 flex items-baseline gap-1.5">
              <span class="text-base font-bold text-orange-600">NT$</span>
              <span class="text-3xl sm:text-4xl font-black text-orange-700 tracking-tight">
                {{ formatNumber(item.current_price) }}
              </span>
            </div>

            <!-- 收藏時間 & 刪除 -->
            <div class="flex items-center justify-between text-xs text-stone-500 border-t border-stone-50 pt-4">
              <div class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span>收藏於 {{ formatDate(item.created_at) }}</span>
              </div>

              <button
                @click="handleRemove(item.id)"
                class="text-stone-400 hover:text-red-500 hover:scale-110 transition-all p-1.5 rounded-full hover:bg-red-50"
                title="移除收藏"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 底部動作條 -->
          <a
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="mt-auto bg-gradient-to-r from-stone-50 to-amber-50 hover:from-orange-600 hover:to-amber-600 text-zinc-700 hover:text-white px-6 py-4 text-center font-semibold transition-all duration-300 flex items-center justify-center gap-2 border-t border-stone-100 group-hover:border-orange-200"
          >
            查看商品詳情
            <svg class="w-4 h-4 transform group-hover:translate-x-1.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFavorites } from '@/api/client'

const favorites = ref([])
const loading = ref(true)

const formatNumber = (num) => {
  if (num == null) return '0'
  return new Intl.NumberFormat('zh-TW').format(Math.round(num))
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const d = new Date(dateStr)
  if (isNaN(d)) return '未知'
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

const handleRemove = async (id) => {
  if (!confirm('確定要移除此收藏嗎？')) return

  // 樂觀移除
  favorites.value = favorites.value.filter(item => item.id !== id)

  // TODO: 呼叫實際 API 刪除
  // try {
  //   await deleteFavorite(id)
  // } catch (err) {
  //   console.error(err)
  //   alert('移除失敗，請稍後再試')
  //   // 失敗時可還原
  // }
}

onMounted(async () => {
  try {
    const res = await getFavorites()
    favorites.value = Array.isArray(res) ? res : (res.data || [])
  } catch (err) {
    console.error('載入收藏失敗', err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* 強化 line-clamp 在舊瀏覽器的相容性 */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>