import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#FF612B',
        background: '#FAF8F2',
        accent: '#D9F6FA',
        navy: '#002677',
        'brand-gray': '#4B4D4F',
      },
    },
  },
  plugins: [],
}
export default config
