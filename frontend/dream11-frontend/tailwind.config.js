/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#10B981", // Green color for accent
        'dark-background': "#121212",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'nav-item': '0 2px 5px 0 rgba(0,0,0,0.05)',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
