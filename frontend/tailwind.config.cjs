module.exports = {
  darkMode: ["class", ".dark-theme"],
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "'Inter'",
          "'Montserrat'",
          "'Oswald'",
          "'General Sans'",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "'Segoe UI'",
          "Helvetica",
          "Arial",
          "sans-serif"
        ],
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
