import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(fileURLToPath(import.meta.url))
function readAdminKey() {
  try {
    const text = readFileSync(resolve(root, '../backend/.env'), 'utf8')
    const line = text.split(/\r?\n/).filter((item) => /^\s*ADMIN_API_KEY\s*=/.test(item)).at(-1)
    return line ? line.substring(line.indexOf('=') + 1).trim().replace(/^['"]|['"]$/g, '') : ''
  } catch {
    return ''
  }
}
const adminKey = readAdminKey()

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure(proxy) {
          proxy.on('proxyReq', (request) => {
            if (adminKey) request.setHeader('X-Admin-API-Key', adminKey)
          })
        },
      },
    },
  },
})
