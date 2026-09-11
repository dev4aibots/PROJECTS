import type { NextConfig } from 'next';
const config: NextConfig = {
  poweredByHeader: false,
  productionBrowserSourceMaps: false,
  // Small-container friendly: single worker keeps peak memory under ~1 GB sandboxes.
  experimental: { cpus: 1 },
  async headers() {
    return [{ source: '/:path*', headers: [
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      { key: 'X-Frame-Options', value: 'DENY' },
    ] }];
  },
};
export default config;
