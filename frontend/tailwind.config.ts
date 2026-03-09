import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        taxodo: {
          primary: "#0B3C49",
          "primary-hover": "#0A3440",
          "primary-active": "#082B35",
          secondary: "#167C8A",
          accent: "#6AD4B3",
          cta: "#FFB347",
          ink: "#1B2A2F",
          muted: "#5C6B73",
          border: "#E2E8EC",
          surface: "#FFFFFF",
          page: "#F4F7F9",
          subtle: "#EDF2F5",
          success: "#2EAD7B",
          warning: "#F4A259",
          danger: "#E45757",
          info: "#2D9CDB",
          chart1: "#0B3C49",
          chart2: "#167C8A",
          chart3: "#6AD4B3",
          chart4: "#FFB347",
          chart5: "#2D9CDB",
          chart6: "#7A6FF0",
        },
      },
      fontFamily: {
        sans: ["var(--font-source-sans-3)", "system-ui", "sans-serif"],
        heading: ["var(--font-manrope)", "var(--font-source-sans-3)", "sans-serif"],
      },
      maxWidth: {
        content: "1200px",
      },
      borderRadius: {
        sm: "6px",
        md: "12px",
        lg: "16px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 24, 40, 0.08)",
        modal: "0 12px 24px rgba(16, 24, 40, 0.16)",
      },
      keyframes: {
        "fade-slide-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-slide-in": "fade-slide-in 120ms ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
