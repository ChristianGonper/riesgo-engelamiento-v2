/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#080A10',
        frost: 'rgba(255, 255, 255, 0.03)',
        'frost-border': 'rgba(255, 255, 255, 0.1)',
        safe: '#00E676',
        caution: '#FFD600',
        severe: '#FF1744',
        info: '#00B0FF'
      },
      fontFamily: {
        ui: ['Inter', 'sans-serif'],
        telemetry: ['Roboto Mono', 'monospace']
      }
    },
  },
  plugins: [],
}
