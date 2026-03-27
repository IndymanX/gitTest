/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // AInewsroom brand colors
        brand: {
          primary: '#7C3AED',   // violet-600
          secondary: '#10B981', // emerald-500
          accent: '#F59E0B',    // amber-500
          danger: '#EF4444',    // red-500
          warning: '#F59E0B',   // amber-500
          safe: '#10B981',      // emerald-500
        },
      },
      fontFamily: {
        sans: ['Sarabun', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
