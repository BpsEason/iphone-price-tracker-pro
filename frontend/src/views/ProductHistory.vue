<template>
  <div class="min-h-screen bg-gradient-to-b from-stone-50 via-stone-100 to-amber-50/30 text-zinc-800 p-4 sm:p-6 md:p-8 font-sans">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 mb-10 md:mb-12">
        <div>
          <h1 class="text-3xl sm:text-4xl md:text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-amber-600 via-orange-600 to-rose-600 tracking-tight">
            {{ modelName }} 價格趨勢
          </h1>
          <p class="mt-2 text-stone-600 text-base sm:text-lg">
            每小時自動更新 • 捕捉最佳入手時機
          </p>
        </div>

        <button
          @click="goBack"
          class="group inline-flex items-center gap-2 px-6 py-3 bg-white border border-stone-200 rounded-xl text-stone-700 hover:text-orange-700 hover:border-orange-300 hover:bg-orange-50/80 transition-all duration-300 shadow-md hover:shadow-lg active:scale-95"
        >
          <svg class="w-5 h-5 transform group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回列表
        </button>
      </div>

      <!-- 錯誤訊息 -->
      <div v-if="error" class="mb-8 p-6 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-center shadow-sm">
        {{ error }}
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 xl:gap-8">
        <!-- 統計卡片 -->
        <div class="lg:col-span-1 space-y-5">
          <StatCard
            title="當前最低價"
            :value="`NT$${stats.currentMin.toLocaleString()}`"
            color="emerald"
            icon="↓"
          />
          <StatCard
            title="歷史最高價"
            :value="`NT$${stats.max.toLocaleString()}`"
            color="red"
            icon="↑"
          />
          <StatCard
            title="最大跌幅"
            :value="`${stats.dropRate}%`"
            color="orange"
            icon="↘"
          />
        </div>

        <!-- 圖表區域 -->
        <div class="lg:col-span-3 bg-white/80 backdrop-blur-md rounded-3xl border border-stone-200 shadow-xl shadow-stone-200/30 overflow-hidden relative min-h-[450px] sm:min-h-[550px]">
          <!-- 載入中 -->
          <div v-if="loading" class="absolute inset-0 flex flex-col items-center justify-center bg-stone-50/70 z-10 backdrop-blur-sm">
            <div class="relative mb-6">
              <div class="h-16 w-16 border-4 border-amber-100 border-t-amber-600 rounded-full animate-spin"></div>
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="h-8 w-8 bg-amber-500/20 rounded-full animate-ping"></div>
              </div>
            </div>
            <p class="text-lg text-stone-600 font-medium">正在載入價格軌跡...</p>
          </div>

          <!-- 無資料 -->
          <div v-else-if="!hasData" class="absolute inset-0 flex flex-col items-center justify-center text-stone-500">
            <div class="text-7xl mb-4 opacity-70">📉</div>
            <p class="text-xl font-medium">暫無價格歷史資料</p>
            <p class="mt-2 text-stone-600">可能尚未收集到此型號的價格變化</p>
          </div>

          <div class="p-4 sm:p-6 h-full">
            <canvas id="priceChart" class="w-full h-full"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive, onUnmounted, defineComponent, watch } from 'vue'
import Chart from 'chart.js/auto'
import { useRouter } from 'vue-router'

const router = useRouter()
const props = defineProps(['id'])

const modelName = ref('載入中...')
const loading = ref(true)
const error = ref('')
const hasData = ref(false)
const stats = reactive({ currentMin: 0, max: 0, dropRate: 0 })
let chartInstance = null

// 統計卡片子組件（暖色版）
const StatCard = defineComponent({
  props: ['title', 'value', 'color', 'icon'],
  template: `
    <div class="bg-white/90 backdrop-blur-sm p-6 rounded-2xl border border-stone-200 shadow-md hover:shadow-xl hover:border-amber-200 transition-all duration-300">
      <div class="flex items-center justify-between mb-3">
        <p class="text-sm text-stone-600 font-medium">{{ title }}</p>
        <span :class="\`text-2xl font-bold text-\${color}-600\`">{{ icon }}</span>
      </div>
      <p class="text-3xl sm:text-4xl font-mono font-extrabold" :class="\`text-\${color}-700\`">
        {{ value }}
      </p>
    </div>
  `
})

const goBack = () => {
  router.back()
}

const fetchHistory = async () => {
  if (!props.id) {
    error.value = '未收到產品 ID，請返回重試'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''
  hasData.value = false

  try {
    const response = await fetch(`/api/products/${props.id}/history`)
    if (!response.ok) {
      throw new Error(response.status === 404 ? '此產品暫無歷史資料' : '伺服器錯誤')
    }

    const data = await response.json()

    modelName.value = data.model_name || '未知型號'
    const history = data.history || []

    if (history.length > 0) {
      hasData.value = true
      renderChart(history)
      calculateStats(history)
    }
  } catch (err) {
    console.error('無法載入歷史價格', err)
    error.value = err.message || '資料載入失敗，請稍後再試'
  } finally {
    loading.value = false
  }
}

const renderChart = (history) => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const ctx = document.getElementById('priceChart')?.getContext('2d')
  if (!ctx) return

  const labels = [...new Set(history.map(h => h.date))].sort()
  const platforms = [...new Set(history.map(h => h.platform))]
  // 暖色系調色盤，與收藏頁一致
  const colors = ['#f59e0b', '#ea580c', '#dc2626', '#c2410c', '#b45309', '#9a3412']

  const datasets = platforms.map((plat, index) => {
    const platformData = labels.map(date => {
      const record = history.find(h => h.platform === plat && h.date === date)
      return record ? record.price : null
    })

    return {
      label: plat,
      data: platformData,
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '22',  // 透明度 13%
      tension: 0.4,
      fill: true,
      borderWidth: 3,
      spanGaps: true,
      pointRadius: 4,
      pointHoverRadius: 7
    }
  })

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        title: {
          display: true,
          text: '多平台價格走勢比較',
          color: '#44403c',
          font: { size: 18, weight: 'bold' },
          padding: { top: 10, bottom: 20 }
        },
        legend: {
          position: 'top',
          labels: { color: '#57534e', usePointStyle: true, padding: 20, font: { size: 13 } }
        },
        tooltip: {
          backgroundColor: 'rgba(250, 250, 250, 0.95)',
          titleColor: '#1f2937',
          bodyColor: '#4b5563',
          borderColor: '#d6d3d1',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#6b7280', maxTicksLimit: 12 }
        },
        y: {
          grid: { color: '#e5e7eb' },
          ticks: {
            color: '#6b7280',
            callback: v => 'NT$' + v.toLocaleString()
          }
        }
      }
    }
  })
}

const calculateStats = (history) => {
  if (!history.length) return
  const prices = history.map(h => h.price).filter(p => p != null)
  if (!prices.length) return

  stats.max = Math.max(...prices)
  stats.currentMin = prices[prices.length - 1]
  stats.dropRate = stats.max > 0 ? (((stats.max - stats.currentMin) / stats.max) * 100).toFixed(1) : '0.0'
}

watch(() => props.id, (newId, oldId) => {
  if (newId && newId !== oldId) fetchHistory()
})

onMounted(fetchHistory)

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>