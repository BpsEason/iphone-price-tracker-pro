<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-6 text-center">
    <h1 class="text-8xl font-bold text-slate-800 mb-4">404</h1>
    <p class="text-2xl text-slate-600 mb-8">頁面不存在</p>
    <router-link 
      to="/" 
      class="px-8 py-4 bg-indigo-600 text-white text-lg font-medium rounded-xl hover:bg-indigo-700 transition"
    >
      返回首頁
    </router-link>
  </div>
</template>

<script setup>
// 可留空
</script>