import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Used for both `vite dev` (server.proxy) and `vite preview` (preview.proxy)
// so the trycloudflare-tunnel flow (run_with_tunnel.bat) works in either mode.
const proxy = {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    configure: (proxy) => {
      proxy.on('proxyRes', (proxyRes) => {
        const loc = proxyRes.headers.location;
        if (typeof loc === 'string' && /^https?:\/\/[^/]+\//i.test(loc)) {
          proxyRes.headers.location = loc.replace(/^https?:\/\/[^/]+/i, '');
        }
      });
    },
  },
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true,
  },
};

export default defineConfig({
  plugins: [react({
    strictMode: false,
  })],
  server: {
    port: 5173,
    host: true,
    allowedHosts: true,
    proxy,
  },
  preview: {
    port: 5173,
    host: true,
    allowedHosts: true,
    proxy,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
