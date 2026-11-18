export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ['"Public Sans"', "system-ui", "Segoe UI", "Arial", "sans-serif"] },
      colors: {
        brand: { DEFAULT: "#1F5A2E", dark: "#164222", tint: "#E9F2EB" },
        ink: "#1B2430", muted: "#5B6672", paper: "#F4F6F3", line: "#D8DED5",
        warn: { DEFAULT: "#8A5200", tint: "#FBF1DF" }, bad: { DEFAULT: "#A12626", tint: "#FBEAEA" },
      },
    },
  },
  plugins: [],
};
