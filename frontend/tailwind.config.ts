import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Montserrat",
          "Arial",
          "Helvetica",
          "メイリオ",
          "ヒラギノ角ゴ pro w3",
          "sans-serif",
        ],
        heading: [
          "Montserrat",
          "Arial",
          "Helvetica",
          "メイリオ",
          "ヒラギノ角ゴ pro w3",
          "sans-serif",
        ],
      },
      colors: {
        brand: {
          primary: "#97D4C6",
          accent: "#F5CC80",
          background: "#FFFFFF",
          text: "#000000",
          link: "#1D345E",
        },
      },
      borderRadius: {
        brand: "12px",
      },
    },
  },
  plugins: [],
};

export default config;

