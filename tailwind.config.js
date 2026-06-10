module.exports = {
  content: ["./app/templates/**/*.html", "./app/static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f1eefe", 100: "#e7e1ff", 400: "#8b7bff",
          500: "#6d5efc", 600: "#5b4bd6", 700: "#4a3cb8",
        },
      },
      borderRadius: { "2xl": "1.25rem" },
    },
  },
  plugins: [],
};
