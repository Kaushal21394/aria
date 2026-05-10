/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ── Aria Intelligence — Deep Oceanic Dark Mode ─────────────────────
        "background":                 "#001330",
        "surface":                    "#001330",
        "surface-dim":                "#001330",
        "surface-bright":             "#26395b",
        "surface-container-lowest":   "#000d26",
        "surface-container-low":      "#041b3c",
        "surface-container":          "#081f40",
        "surface-container-high":     "#152a4b",
        "surface-container-highest":  "#213557",
        "on-surface":                 "#d7e2ff",
        "on-surface-variant":         "#bfc7d5",
        "on-background":              "#d7e2ff",
        "inverse-surface":            "#d7e2ff",
        "inverse-on-surface":         "#1c3052",
        "surface-variant":            "#213557",
        "surface-tint":               "#9ecaff",
        "outline":                    "#89919e",
        "outline-variant":            "#3f4753",

        // Primary — Electric Blue
        "primary":                    "#9ecaff",
        "on-primary":                 "#003258",
        "primary-container":          "#009afe",
        "on-primary-container":       "#c4dcff",
        "primary-fixed":              "#d1e4ff",
        "primary-fixed-dim":          "#9ecaff",
        "on-primary-fixed":           "#001d36",
        "on-primary-fixed-variant":   "#00497d",
        "inverse-primary":            "#0061a3",

        // Secondary — Royal Blue
        "secondary":                  "#aac7ff",
        "on-secondary":               "#002f65",
        "secondary-container":        "#005ab5",
        "on-secondary-container":     "#c1d5ff",
        "secondary-fixed":            "#d7e3ff",
        "secondary-fixed-dim":        "#aac7ff",
        "on-secondary-fixed":         "#001b3e",
        "on-secondary-fixed-variant": "#00458e",

        // Tertiary — Amethyst Purple (AI intelligence layer)
        "tertiary":                   "#e3b5ff",
        "on-tertiary":                "#4c0974",
        "tertiary-container":         "#ba7ce3",
        "on-tertiary-container":      "#4a0571",
        "tertiary-fixed":             "#f4daff",
        "tertiary-fixed-dim":         "#e3b5ff",
        "on-tertiary-fixed":          "#2f004c",
        "on-tertiary-fixed-variant":  "#65298c",

        // Error
        "error":                      "#ffb4ab",
        "on-error":                   "#690005",
        "error-container":            "#93000a",
        "on-error-container":         "#ffdad6",
      },

      fontFamily: {
        // Body — Inter (max legibility in dense data layouts)
        sans:     ["Inter",         "system-ui", "sans-serif"],
        // Headlines — Manrope (premium, organized, modern)
        headline: ["Manrope",       "system-ui", "sans-serif"],
        // Data labels / numerical readouts — Space Grotesk (geometric, tech feel)
        data:     ["Space Grotesk", "system-ui", "sans-serif"],
        mono:     ["Space Grotesk", "system-ui", "sans-serif"],
      },

      // Rounded — Technical + Precise (8px buttons, 16px cards, 24px agent elements)
      borderRadius: {
        sm:      "0.25rem",   // 4px
        DEFAULT: "0.5rem",    // 8px  — standard buttons & inputs
        md:      "0.75rem",   // 12px
        lg:      "1rem",      // 16px — cards
        xl:      "1.5rem",    // 24px — agent / AI insight elements
        full:    "9999px",
      },

      animation: {
        "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in":    "fadeIn 0.4s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
