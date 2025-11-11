const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('Starting Vercel build process...');

// Install dependencies
console.log('Installing dependencies...');
execSync('npm install --omit=dev', { stdio: 'inherit' });

// Build the UI
console.log('Building UI...');
process.chdir('simple_ui');
execSync('npm ci', { stdio: 'inherit' });
execSync('npm run build', { stdio: 'inherit' });
process.chdir('..');

// Verify build output
const distPath = path.join(__dirname, 'simple_ui', 'dist');
if (!fs.existsSync(distPath)) {
  console.error('❌ Build failed: dist directory not found!');
  process.exit(1);
}

const files = fs.readdirSync(distPath);
if (files.length === 0) {
  console.error('❌ Build failed: dist directory is empty!');
  process.exit(1);
}

console.log('✅ Build completed successfully!');
console.log('📁 Build output:', files.join(', '));
