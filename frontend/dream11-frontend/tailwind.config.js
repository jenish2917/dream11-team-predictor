/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#10B981", // Green color for accent (can be adjusted)
        dark: {
          background: "#121212",
          text: "#FFFFFF",
        },
        light: {
          background: "#FFFFFF",
          text: "#121212",
        }
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
