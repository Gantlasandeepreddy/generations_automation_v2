/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    // Backend URL for server-side proxy
    // Defaults to localhost, override with BACKEND_URL env var
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

    console.log(`[Next.js] Proxying /api/backend/* requests to: ${backendUrl}/api/*`);

    return [
      // Proxy backend API calls to Python FastAPI backend
      // Use /api/backend/* to avoid conflicts with NextAuth /api/auth/*
      {
        source: '/api/backend/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
}

module.exports = nextConfig
