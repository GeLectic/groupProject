/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#f6f0e5",
        parchment: "#2f2414",
        gold: "#bb8a2e",
        emerald: "#1f9a88",
        surface: "#fffdf8",
        mist: "#fff8ed",
        sandstone: "#e5d7bf",
        ink: "#2a2014",
      },
      fontFamily: {
        display: ["Sora", "sans-serif"],
        body: ["Manrope", "sans-serif"],
        ui: ["Outfit", "sans-serif"],
      },
      boxShadow: {
        gold: "0 18px 48px rgba(187, 138, 46, 0.24)",
        soft: "0 10px 36px rgba(90, 66, 28, 0.12)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        floatSlow: {
          "0%, 100%": { transform: "translateY(0px) translateX(0px)" },
          "50%": { transform: "translateY(-16px) translateX(10px)" },
        },
        drift: {
          "0%": { transform: "translateX(-2%) scale(1)" },
          "50%": { transform: "translateX(2%) scale(1.03)" },
          "100%": { transform: "translateX(-2%) scale(1)" },
        },
        breathe: {
          "0%, 100%": { transform: "scale(1)", opacity: "0.95" },
          "50%": { transform: "scale(1.02)", opacity: "1" },
        },
      },
      animation: {
        shimmer: "shimmer 4s linear infinite",
        floatSlow: "floatSlow 9s ease-in-out infinite",
        drift: "drift 14s ease-in-out infinite",
        breathe: "breathe 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
