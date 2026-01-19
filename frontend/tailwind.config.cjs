module.exports = {
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'DM Sans'", "Inter", "sans-serif"],
        body: ["'Inter'", "sans-serif"]
      },
      colors: {
        brand: {
          DEFAULT: "#0ea5e9",
          dark: "#0a7ab8"
        }
      }
    }
  },
  plugins: []
};
