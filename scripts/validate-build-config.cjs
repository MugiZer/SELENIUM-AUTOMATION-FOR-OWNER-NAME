const fs = require('fs');
const path = require('path');

console.log('🔍 Validating build output configuration...\n');

const vercelJson = JSON.parse(fs.readFileSync('vercel.json', 'utf8'));
let hasIssues = false;

// Check builds configuration
console.log('📦 Build Configuration:');
if (vercelJson.builds && Array.isArray(vercelJson.builds)) {
  const staticBuild = vercelJson.builds.find(b => b.use === '@vercel/static-build');
  if (staticBuild) {
    console.log(`  Source: ${staticBuild.src}`);
    console.log(`  Builder: ${staticBuild.use}`);
    if (staticBuild.config && staticBuild.config.distDir) {
      console.log(`  distDir: ${staticBuild.config.distDir}`);
    }
    
    // Verify the package.json exists
    if (staticBuild.src && !fs.existsSync(staticBuild.src)) {
      console.error(`  ❌ Source file not found: ${staticBuild.src}`);
      hasIssues = true;
    } else {
      console.log(`  ✅ Source file exists: ${staticBuild.src}`);
    }
  }
}

// Check outputDirectory
if (vercelJson.outputDirectory) {
  console.log(`\n📁 Output Directory: ${vercelJson.outputDirectory}`);
}

// Check buildCommand
if (vercelJson.buildCommand) {
  console.log(`\n🔨 Build Command: ${vercelJson.buildCommand}`);
}

// Check vite.config.ts for consistency
console.log('\n🔧 Vite Configuration:');
const viteConfigPath = 'simple_ui/vite.config.ts';
if (fs.existsSync(viteConfigPath)) {
  const viteConfig = fs.readFileSync(viteConfigPath, 'utf8');
  
  // Extract outDir (simple regex, may need adjustment for complex configs)
  const outDirMatch = viteConfig.match(/outDir:\s*['"]([^'"]+)['"]/);
  if (outDirMatch) {
    const outDir = outDirMatch[1];
    console.log(`  outDir: ${outDir}`);
    
    // Check consistency
    const expectedOutput = 'simple_ui/dist';
    if (vercelJson.outputDirectory === expectedOutput) {
      console.log(`  ✅ Output directory matches: ${expectedOutput}`);
    } else {
      console.warn(`  ⚠️  Mismatch: vercel.json expects ${vercelJson.outputDirectory}, vite uses ${outDir}`);
    }
  }
  
  // Check base path
  const baseMatch = viteConfig.match(/base:\s*['"]([^'"]+)['"]/);
  if (baseMatch) {
    const base = baseMatch[1];
    console.log(`  base: ${base}`);
    if (base !== '/') {
      console.warn(`  ⚠️  Base path is not root (/). Ensure rewrites are configured correctly.`);
    } else {
      console.log(`  ✅ Base path is root (/)`);
    }
  }
}

// Check if package.json has build script
console.log('\n📜 UI Package Scripts:');
const uiPackageJson = JSON.parse(fs.readFileSync('simple_ui/package.json', 'utf8'));
if (uiPackageJson.scripts && uiPackageJson.scripts.build) {
  console.log(`  build: ${uiPackageJson.scripts.build}`);
  console.log(`  ✅ Build script exists`);
} else {
  console.error(`  ❌ No build script found in simple_ui/package.json`);
  hasIssues = true;
}

// Check for verification script
if (uiPackageJson.scripts && uiPackageJson.scripts['verify-build']) {
  console.log(`  ✅ Build verification script exists`);
}

// Check rewrites for proper routing
console.log('\n🔀 Routing Configuration:');
if (vercelJson.rewrites && Array.isArray(vercelJson.rewrites)) {
  vercelJson.rewrites.forEach((rewrite, idx) => {
    console.log(`  Rewrite ${idx}: ${rewrite.source} -> ${rewrite.destination}`);
  });
  
  // Check for proper fallback to UI
  const uiFallback = vercelJson.rewrites.find(r => 
    r.source === '/(.*)' && r.destination.includes('dist')
  );
  if (uiFallback) {
    console.log(`  ✅ Fallback to UI dist configured`);
  }
  
  // Check API routing
  const apiRoute = vercelJson.rewrites.find(r => 
    r.source.includes('/api/')
  );
  if (apiRoute) {
    console.log(`  ✅ API routing configured`);
  }
}

console.log('\n' + (hasIssues ? '❌ Build config validation FAILED' : '✅ Build config validation PASSED'));
process.exit(hasIssues ? 1 : 0);

