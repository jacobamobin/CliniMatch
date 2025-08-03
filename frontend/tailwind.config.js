/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      backdropBlur: {
        'lg': '16px',
      },
      backgroundColor: {
        'glass': 'rgba(59, 130, 246, 0.1)', // blue glass effect
        'glass-dark': 'rgba(30, 58, 138, 0.2)', // darker blue glass
      },
      borderColor: {
        'glass': 'rgba(96, 165, 250, 0.2)', // blue border
        'glass-light': 'rgba(147, 197, 253, 0.3)', // lighter blue border
      },
      colors: {
        'blue-glass': {
          50: 'rgba(239, 246, 255, 0.1)',
          100: 'rgba(219, 234, 254, 0.1)',
          200: 'rgba(191, 219, 254, 0.1)',
          300: 'rgba(147, 197, 253, 0.1)',
          400: 'rgba(96, 165, 250, 0.1)',
          500: 'rgba(59, 130, 246, 0.1)',
          600: 'rgba(37, 99, 235, 0.1)',
          700: 'rgba(29, 78, 216, 0.1)',
          800: 'rgba(30, 64, 175, 0.1)',
          900: 'rgba(30, 58, 138, 0.1)',
        }
      }
    },
  },
  plugins: [],
}