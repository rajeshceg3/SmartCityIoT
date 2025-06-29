/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './citizen_reporting/templates/**/*.html',
    './traffic_management/templates/**/*.html',
    './waste_management/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3B82F6', // Blue-500
          dark: '#2563EB',   // Blue-600
        },
        secondary: {
          DEFAULT: '#6B7280', // Gray-500
          light: '#D1D5DB', // Gray-300
          dark: '#4B5563',  // Gray-600
          darker: '#374151', // Gray-700, for headings or darker text
          lightest: '#F9FAFB', // Gray-50, for very light backgrounds/striping
        },
        success: {
          DEFAULT: '#10B981', // Green-500
          dark: '#059669',   // Green-600
        },
        error: {
          DEFAULT: '#EF4444',   // Red-500
          dark: '#DC2626',    // Red-600
        },
        warning: {
          DEFAULT: '#F59E0B', // Yellow-500
          dark: '#D97706',   // Yellow-600 (Amber-600)
        },
        info: {
          DEFAULT: '#6366F1',    // Indigo-500
          dark: '#4F46E5',     // Indigo-600
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
