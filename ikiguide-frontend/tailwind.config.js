/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ikigai-main': '#37715B',
        'ikigai-secondary': '#D5AF37',
        'ikigai-tertiary': '#5C7C95',
        'ikigai-accent1': '#A14B2A',
        'ikigai-accent2': '#9A6FB0',
        'ikigai-grey': '#A3A3A3',
        'ikigai-black': '#232222'
      }
    },
  },
  plugins: [],
}
