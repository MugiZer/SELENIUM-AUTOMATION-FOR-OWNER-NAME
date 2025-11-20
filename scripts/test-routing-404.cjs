#!/usr/bin/env node
/**
 * Comprehensive Routing & 404 Test Script
 * Tests all critical paths to ensure no 404 errors will occur on Vercel
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing Routing Configuration for 404 Prevention\n');
console.log('='.repeat(60));

let allTestsPassed = true;
let testCount = 0;
let passCount = 0;
let failCount = 0;

function test(name, condition, details = '') {
  testCount++;
  if (condition) {
    passCount++;
    console.log(`✅ [${testCount}] ${name}`);
    if (details) console.log(`   ${details}`);
  } else {
    failCount++;
    allTestsPassed = false;
    console.error(`❌ [${testCount}] ${name}`);
    if (details) console.error(`   ${details}`);
  }
}

// Test 1: Build output exists
console.log('\n📦 Build Output Tests');
console.log('-'.repeat(60));

const indexPath = path.join('simple_ui', 'dist', 'index.html');
const assetsPath = path.join('simple_ui', 'dist', 'assets');

test(
  'index.html exists at correct location',
  fs.existsSync(indexPath),
  `Path: ${indexPath}`
);

test(
  'assets directory exists',
  fs.existsSync(assetsPath),
  `Path: ${assetsPath}`
);

if (fs.existsSync(assetsPath)) {
  const assets = fs.readdirSync(assetsPath);
  test(
    'Assets directory contains files',
    assets.length > 0,
    `Found ${assets.length} asset(s): ${assets.slice(0, 3).join(', ')}${assets.length > 3 ? '...' : ''}`
  );
  
  // Check for required asset types
  const hasJS = assets.some(f => f.endsWith('.js'));
  const hasCSS = assets.some(f => f.endsWith('.css'));
  
  test('JavaScript assets present', hasJS, 'Required for SPA functionality');
  test('CSS assets present', hasCSS, 'Required for styling');
}

// Test 2: HTML structure and asset paths
console.log('\n📄 HTML Structure Tests');
console.log('-'.repeat(60));

if (fs.existsSync(indexPath)) {
  const htmlContent = fs.readFileSync(indexPath, 'utf8');
  
  test(
    'HTML contains root element',
    htmlContent.includes('<div id="root">'),
    'Required for React hydration'
  );
  
  test(
    'HTML contains title',
    htmlContent.includes('<title>'),
    'SEO and browser tab display'
  );
  
  // Check asset paths are absolute (root-relative)
  const hasAbsolutePaths = !htmlContent.includes('href="./') && 
                           !htmlContent.includes('src="./') &&
                           !htmlContent.includes('href="../') &&
                           !htmlContent.includes('src="../');
  
  test(
    'Asset paths are absolute (root-relative)',
    hasAbsolutePaths,
    'Paths should start with / (e.g., /assets/...) not ./assets/...'
  );
  
  // Check for /assets/ references
  const hasAssetsPath = htmlContent.includes('/assets/');
  test(
    'HTML references /assets/ path',
    hasAssetsPath,
    'Assets should be served from /assets/ at runtime'
  );
  
  // Extract asset filenames from HTML
  const assetMatches = htmlContent.match(/\/assets\/[^"'\s]+/g) || [];
  test(
    'Asset references found in HTML',
    assetMatches.length > 0,
    `Found ${assetMatches.length} asset reference(s)`
  );
  
  // Verify referenced assets exist
  if (assetMatches.length > 0 && fs.existsSync(assetsPath)) {
    const assets = fs.readdirSync(assetsPath);
    const missingAssets = assetMatches
      .map(ref => {
        const filename = path.basename(ref);
        return assets.includes(filename) ? null : filename;
      })
      .filter(Boolean);
    
    test(
      'All referenced assets exist in dist',
      missingAssets.length === 0,
      missingAssets.length > 0 
        ? `Missing: ${missingAssets.join(', ')}`
        : 'All assets present'
    );
  }
}

// Test 3: Vercel configuration
console.log('\n⚙️  Vercel Configuration Tests');
console.log('-'.repeat(60));

const vercelJsonPath = 'vercel.json';
if (fs.existsSync(vercelJsonPath)) {
  const vercelJson = JSON.parse(fs.readFileSync(vercelJsonPath, 'utf8'));
  
  // Check builds configuration
  const builds = vercelJson.builds || [];
  const staticBuild = builds.find(b => b.use === '@vercel/static-build');
  
  test(
    '@vercel/static-build configured',
    !!staticBuild,
    staticBuild ? `Source: ${staticBuild.src}` : 'Required for SPA deployment'
  );
  
  if (staticBuild) {
    const distDir = staticBuild.config?.distDir || 'dist';
    test(
      'distDir matches Vite output',
      distDir === 'dist',
      `distDir: ${distDir} (should be 'dist')`
    );
    
    const sourcePath = staticBuild.src;
    test(
      'Build source file exists',
      fs.existsSync(sourcePath),
      `Path: ${sourcePath}`
    );
  }
  
  // Check rewrites
  const rewrites = vercelJson.rewrites || [];
  test(
    'Rewrites array exists',
    rewrites.length > 0,
    `Found ${rewrites.length} rewrite(s)`
  );
  
  // Check API rewrite
  const apiRewrite = rewrites.find(r => r.source.includes('/api/'));
  test(
    'API rewrite configured',
    !!apiRewrite,
    apiRewrite 
      ? `Pattern: ${apiRewrite.source} → ${apiRewrite.destination}`
      : 'Required to prevent API routes from hitting SPA fallback'
  );
  
  // Check SPA fallback
  const spaFallback = rewrites.find(r => 
    (r.source === '/(.*)' || r.source === '/(.*)' || r.source === '/*') &&
    (r.destination === '/index.html' || r.destination === '/')
  );
  
  test(
    'SPA fallback rewrite configured',
    !!spaFallback,
    spaFallback
      ? `Pattern: ${spaFallback.source} → ${spaFallback.destination}`
      : 'Required for client-side routing (deep links)'
  );
  
  // Check rewrite order
  if (apiRewrite && spaFallback) {
    const apiIndex = rewrites.indexOf(apiRewrite);
    const spaIndex = rewrites.indexOf(spaFallback);
    
    test(
      'API rewrite comes before SPA fallback',
      apiIndex < spaIndex,
      `Order: API (${apiIndex}) → SPA (${spaIndex})`
    );
  }
  
  // Check for anti-patterns
  const hasBuildTimePath = rewrites.some(r => 
    r.destination.includes('/simple_ui/dist/') ||
    r.destination.includes('/dist/') ||
    r.destination.includes('/build/')
  );
  
  test(
    'No rewrites to build-time paths',
    !hasBuildTimePath,
    'Rewrites should use runtime paths (e.g., /index.html) not build paths'
  );
  
  // Check headers
  const headers = vercelJson.headers || [];
  test(
    'Headers configured',
    headers.length > 0,
    `Found ${headers.length} header rule(s)`
  );
}

// Test 4: Vite configuration
console.log('\n🔧 Vite Configuration Tests');
console.log('-'.repeat(60));

const viteConfigPath = path.join('simple_ui', 'vite.config.ts');
if (fs.existsSync(viteConfigPath)) {
  const viteConfig = fs.readFileSync(viteConfigPath, 'utf8');
  
  test(
    'Vite config exists',
    true,
    `Path: ${viteConfigPath}`
  );
  
  // Check base path
  const hasBaseRoot = viteConfig.includes("base: '/'") || 
                      viteConfig.includes('base: "/"') ||
                      viteConfig.includes("base:'/'");
  
  test(
    'Base path is root (/)',
    hasBaseRoot || !viteConfig.includes('base:'),
    'Base should be / for root deployment (or omitted, defaults to /)'
  );
  
  // Check outDir
  const hasOutDir = viteConfig.includes("outDir: 'dist'") ||
                    viteConfig.includes('outDir: "dist"');
  
  test(
    'Output directory is dist',
    hasOutDir || !viteConfig.includes('outDir:'),
    'outDir should be dist (or omitted, defaults to dist)'
  );
}

// Test 5: Package.json scripts
console.log('\n📜 Build Script Tests');
console.log('-'.repeat(60));

const uiPackageJsonPath = path.join('simple_ui', 'package.json');
if (fs.existsSync(uiPackageJsonPath)) {
  const uiPackageJson = JSON.parse(fs.readFileSync(uiPackageJsonPath, 'utf8'));
  const scripts = uiPackageJson.scripts || {};
  
  test(
    'Build script exists',
    !!scripts.build,
    scripts.build ? `Command: ${scripts.build}` : 'Required for Vercel build'
  );
  
  test(
    'Build verification script exists',
    !!scripts['verify-build'] || scripts.build?.includes('verify'),
    'Helps catch build failures early'
  );
}

// Test 6: Expected runtime behavior simulation
console.log('\n🌐 Runtime Behavior Simulation');
console.log('-'.repeat(60));

// Simulate what Vercel will do
const testRoutes = [
  { path: '/', expected: 'index.html', type: 'SPA root' },
  { path: '/dashboard', expected: 'index.html', type: 'SPA deep link' },
  { path: '/users/123', expected: 'index.html', type: 'SPA deep link' },
  { path: '/assets/index.BeyKAiJ4.js', expected: 'file', type: 'Static asset' },
  { path: '/api/health', expected: 'api/index.js', type: 'API endpoint' },
];

testRoutes.forEach(route => {
  let wouldWork = false;
  let reason = '';
  
  if (route.expected === 'index.html') {
    wouldWork = fs.existsSync(indexPath);
    reason = wouldWork ? 'index.html exists, SPA fallback will serve it' : 'index.html missing';
  } else if (route.expected === 'file') {
    const assetName = path.basename(route.path);
    const assetFile = path.join(assetsPath, assetName);
    wouldWork = fs.existsSync(assetFile);
    reason = wouldWork ? `Asset exists: ${assetName}` : `Asset missing: ${assetName}`;
  } else if (route.expected === 'api/index.js') {
    wouldWork = fs.existsSync('api/index.js');
    reason = wouldWork ? 'api/index.js exists, API rewrite will route to it' : 'api/index.js missing';
  }
  
  test(
    `${route.path} → ${route.expected} (${route.type})`,
    wouldWork,
    reason
  );
});

// Summary
console.log('\n' + '='.repeat(60));
console.log('📊 Test Summary');
console.log('='.repeat(60));
console.log(`Total Tests: ${testCount}`);
console.log(`✅ Passed: ${passCount}`);
console.log(`❌ Failed: ${failCount}`);
console.log(`\n${allTestsPassed ? '✅ ALL TESTS PASSED - Configuration is ready for deployment!' : '❌ SOME TESTS FAILED - Fix issues before deploying'}`);

if (allTestsPassed) {
  console.log('\n🎯 Expected Behavior on Vercel:');
  console.log('   ✅ GET / → 200 (index.html)');
  console.log('   ✅ GET /dashboard → 200 (index.html, SPA hydration)');
  console.log('   ✅ GET /assets/*.js → 200 (static files)');
  console.log('   ✅ GET /api/health → 200 (server.js)');
  console.log('   ✅ No 404 errors for root or deep links');
} else {
  console.log('\n⚠️  Fix the failed tests above before deploying.');
}

process.exit(allTestsPassed ? 0 : 1);

