import {defineConfig, devices} from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false,
  retries: 0,
  reporter: 'line',
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'retain-on-failure',
  },
  projects: [{name: 'chromium', use: {...devices['Desktop Chrome']}}],
  webServer: [
    {
      command: '../.venv/bin/uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/api/health',
      env: {
        PROVIDER_MODE: 'deterministic',
        AUTH_MODE: 'deterministic',
        CORS_ORIGINS: 'http://127.0.0.1:3000',
      },
      reuseExistingServer: false,
    },
    {
      command: 'NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000',
      url: 'http://127.0.0.1:3000',
      reuseExistingServer: false,
    },
  ],
});
