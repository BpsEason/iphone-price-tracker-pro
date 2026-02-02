<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50/30 flex items-center justify-center p-4 sm:p-6">
    <div class="w-full max-w-md">
      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100">
        <!-- Header -->
        <div class="px-8 pt-10 pb-6 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white text-center">
          <h1 class="text-3xl font-bold tracking-tight">登入 iPhone Pro Tracker</h1>
          <p class="mt-2 text-indigo-100 opacity-90">
            開始追蹤你最愛的 iPhone 價格
          </p>
        </div>

        <!-- Form -->
        <div class="p-8 sm:p-10">
          <form @submit.prevent="handleLogin" class="space-y-6">
            <!-- Email -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">
                電子郵件
              </label>
              <input
                v-model="email"
                type="email"
                placeholder="your@email.com"
                required
                autocomplete="email"
                class="w-full px-4 py-3 rounded-lg border border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all text-slate-800 placeholder-slate-400"
              />
            </div>

            <!-- Password -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">
                密碼
              </label>
              <div class="relative">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  required
                  autocomplete="current-password"
                  class="w-full px-4 py-3 rounded-lg border border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all text-slate-800 placeholder-slate-400 pr-11"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 focus:outline-none"
                >
                  <svg
                    v-if="showPassword"
                    class="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:ring-offset-2 transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="loading" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
              {{ loading ? '登入中...' : '登入' }}
            </button>
          </form>

          <!-- Error Message -->
          <div
            v-if="errorMessage"
            class="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-center text-sm"
          >
            {{ errorMessage }}
          </div>

          <!-- Footer Links (可選) -->
          <div class="mt-6 text-center text-sm text-slate-500">
            還沒有帳號？ 
            <router-link
              to="/register"
              class="text-indigo-600 hover:text-indigo-800 font-medium hover:underline"
            >
              立即註冊
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'
import { useRouter } from 'vue-router'

const router = useRouter()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    const params = new URLSearchParams()
    params.append('username', email.value.trim())
    params.append('password', password.value)

    const { data } = await api.post('/v1/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })

    localStorage.setItem('access_token', data.access_token)
    
    // 可選：儲存使用者資訊或其他 token
    // localStorage.setItem('user', JSON.stringify(data.user))

    // 登入成功後跳轉
    router.push('/favorites') // 或 '/'

  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '帳號或密碼錯誤，請再試一次'
  } finally {
    loading.value = false
  }
}
</script>