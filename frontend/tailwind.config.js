/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        canvas: '#F8FAFC',
        accent: {
          blue: '#3B82F6',
          green: '#10B981',
          purple: '#8B5CF6',
          orange: '#F97316',
          amber: '#F59E0B',
          cyan: '#06B6D4',
        }
      },
      animation: {
        'pulse-subtle': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-danger': 'dangerPulse 1.2s infinite',
        'flow-dash': 'flowDash 1.5s linear infinite',
      },
      keyframes: {
        dangerPulse: {
          '0%, 100%': { borderColor: 'rgba(239, 68, 68, 1)', boxShadow: '0 0 15px rgba(239, 68, 68, 0.5)' },
          '50%': { borderColor: 'rgba(239, 68, 68, 0.4)', boxShadow: '0 0 5px rgba(239, 68, 68, 0.2)' },
        },
        flowDash: {
          from: { strokeDashoffset: '24' },
          to: { strokeDashoffset: '0' },
        }
      }
    },
  },
  plugins: [],
}
