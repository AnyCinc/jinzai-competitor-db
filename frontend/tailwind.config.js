/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        neutral: {
          850: '#1c1c1c',
          925: '#0d0d0d',
          950: '#080808',
        },
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'serif'],
        sans: ['"Noto Sans JP"', 'Montserrat', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
