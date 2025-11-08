import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  base: '/', // Use root-relative paths for Vercel
  plugins: [react()],
  // Ensure consistent base URL for all assets
  define: {
    'import.meta.env.BASE_URL': JSON.stringify('/'),
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: true,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor and app code
          vendor: ['react', 'react-dom'],
        },
        // Ensure consistent hashing for better caching
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash][extname]',
        // Ensure absolute paths for all assets
        paths: (id) => {
          if (id.includes('node_modules')) {
            return id;
          }
          return `/${id}`;
        },
      },
    },
  },
});
