module.exports = {
  darkMode: ["class", ".dark-theme"],
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'DM Sans'", "Inter", "sans-serif"],
        body: ["'Inter'", "sans-serif"]
      },
      colors: {
        brand: {
          DEFAULT: "#41ce5f",
          dark: "#2f9e49"
        }
      }
    }
  },
  plugins: []
};
