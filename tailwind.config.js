/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0b101a',
        surface: '#111827',
        surfaceMuted: '#1b2333',
        border: 'rgba(148, 163, 184, 0.12)',
        accent: '#38bdf8',
        accentMuted: '#0ea5e9',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        'grid-line': 'rgba(148, 163, 184, 0.08)',
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"Fira Code"', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 30px rgba(56, 189, 248, 0.15)',
        inner: 'inset 0 0 0 1px rgba(148, 163, 184, 0.1)',
      },
      backgroundImage: {
        'grid-overlay':
          'radial-gradient(circle at center, rgba(56, 189, 248, 0.12) 0, transparent 60%), linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px), linear-gradient(0deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px)',
      },
      animation: {
        pulseSlow: 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        pingSlow: 'ping 3s cubic-bezier(0, 0, 0.2, 1) infinite',
        'marquee-slow': 'marquee 30s linear infinite',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms'), require('@tailwindcss/typography')],
}
