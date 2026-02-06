import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          900: "#0a0e17",
          800: "#111827",
          700: "#1a2234",
          600: "#243049",
          500: "#2d3b58",
        },
        text: {
          primary: "#f0f4fc",
          secondary: "#94a3c4",
          muted: "#5b6b8a",
        },
        accent: {
          DEFAULT: "#3b82f6",
          hover: "#60a5fa",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "slide-in-right":
          "slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-in-up":
          "slideInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "fade-in": "fadeIn 0.2s ease-out forwards",
      },
      keyframes: {
        slideInRight: {
          from: { transform: "translateX(20px)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        slideInUp: {
          from: { transform: "translateY(10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      boxShadow: {
        glass: "0 4px 30px rgba(0, 0, 0, 0.3)",
        "glass-lg": "0 8px 40px rgba(0, 0, 0, 0.4)",
      },
    },
  },
  plugins: [],
};

export default config;
