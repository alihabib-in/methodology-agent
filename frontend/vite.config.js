import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const certDir = path.resolve(here, '../jitsi/config/storage/web/keys');

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // expose on the network so other participants can join
    port: 5173,
    https: {
      key: fs.readFileSync(path.join(certDir, 'cert.key')),
      cert: fs.readFileSync(path.join(certDir, 'cert.crt')),
    },
    // Proxy API calls through the dev server (same origin) so the browser
    // never issues mixed-content requests to the backend.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/meetings': 'http://127.0.0.1:8000',
      '/knowledge': 'http://127.0.0.1:8000',
      '/tts': 'http://127.0.0.1:8000',
      '/cases': 'http://127.0.0.1:8000',
      '/ws': { target: 'http://127.0.0.1:8000', ws: true },
    },
  },
});
