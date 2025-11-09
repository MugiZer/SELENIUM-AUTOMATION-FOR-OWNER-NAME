import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables based on the current mode (development/production)
  const env = loadEnv(mode, process.cwd(), '');
  const isDev = mode === 'development';
  
  return {
    // Always use root-relative paths for Vercel
    base: '/',
    plugins: [react()],
    define: {
      'import.meta.env.BASE_URL': JSON.stringify('/'),
      'import.meta.env.API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || 'http://localhost:3000')
    },
    server: {
      port: 5173,
      proxy: isDev ? {
        // Proxy API requests to the backend server in development
        '^/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:3000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, '/api')
        }
      } : undefined
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, './src')
      }
    },
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: isDev,
      rollupOptions: {
        output: {
          entryFileNames: 'assets/[name].[hash].js',
          chunkFileNames: 'assets/[name].[hash].js',
          assetFileNames: 'assets/[name].[hash].[ext]',
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled']
          }
        }
      }
    }
  }
});
