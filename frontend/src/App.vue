<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-900">
    <header class="bg-white border-b sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <h1 class="text-xl font-bold tracking-tight text-brand-dark flex items-center gap-2">
          <router-link to="/" class="flex items-center gap-2">
            <span class="p-2 bg-brand-primary text-white rounded-lg shadow-sm">📊</span>
            iPhone Pro Tracker
          </router-link>
        </h1>
        <router-link to="/favorites" class="text-slate-600 hover:text-brand-primary px-4 py-2 text-sm font-medium transition-colors">
          ❤️ 我的收藏
        </router-link>
      </div>
    </header>

    <router-view />
  </div>
</template>