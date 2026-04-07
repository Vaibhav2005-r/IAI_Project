/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'deep-blue': {
          DEFAULT: '#0047AB',
          900: '#001b3a',
          800: '#00295c',
          700: '#003682',
          600: '#0043a3',
          500: '#0055d4',
          400: '#2b7fff',
          300: '#5c9fff',
          200: '#8ebfff',
          100: '#c2ddff',
          50: '#e6f0ff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
