/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        entry: "#16a34a",
        internal: "#2563eb",
        exit: "#dc2626",
      },
    },
  },
  plugins: [],
};
