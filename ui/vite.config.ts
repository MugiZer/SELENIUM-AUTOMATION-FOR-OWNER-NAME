import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { fileURLToPath } from 'url';
import { componentTagger } from "lovable-tagger";

// Get directory name in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current directory.
  const env = loadEnv(mode, process.cwd(), '');

  // Filter out all environment variables except those prefixed with VITE_
  const processEnv: Record<string, string> = {};
  Object.entries(env).forEach(([key, value]) => {
    if (key.startsWith('VITE_')) {
      processEnv[`process.env.${key}`] = JSON.stringify(value);
    }
  });

  return {
    define: {
      ...processEnv,
      'process.env.NODE_ENV': JSON.stringify(mode),
      'process.env': { ...env, NODE_ENV: mode }
    },
    base: '/',
    server: {
      host: "::",
      port: 8080,
      strictPort: true,
      fs: {
        strict: false
      }
    },
    preview: {
      port: 8080,
      strictPort: true,
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: mode !== 'production',
      minify: mode === 'production' ? 'esbuild' : false,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom', 'react-router-dom'],
            ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          },
        },
      },
    },
    plugins: [
      react(),
      mode === "development" && componentTagger()
    ].filter(Boolean) as any[],
    resolve: {
      alias: [
        { find: '@', replacement: path.resolve(__dirname, 'src') },
        { find: '@components', replacement: path.resolve(__dirname, 'src/components') },
        { find: '@lib', replacement: path.resolve(__dirname, 'src/lib') },
        { find: '@pages', replacement: path.resolve(__dirname, 'src/pages') },
      ],
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    optimizeDeps: {
      include: ['@/lib/utils']
    }
  };
});
