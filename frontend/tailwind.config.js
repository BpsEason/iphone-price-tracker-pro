/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#0EA5E9', // 攝影師配色：天空藍
        'brand-dark': '#0F172A',    // 質感深藍
      }
    },
  },
  plugins: [],
}
