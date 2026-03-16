/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        threat: {
          critical: '#dc2626',
          high: '#ea580c',
          medium: '#d97706',
          low: '#65a30d',
          info: '#0284c7',
        },
      },
    },
  },
  plugins: [],
}
