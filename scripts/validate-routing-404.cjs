const fs = require('fs');

console.log('🔍 Validating routing configuration for 404 prevention...\n');

const vercelJson = JSON.parse(fs.readFileSync('vercel.json', 'utf8'));
let hasIssues = false;

// Check if using builds array with @vercel/static-build
const staticBuild = vercelJson.builds?.find(b => b.use === '@vercel/static-build');

if (staticBuild) {
  console.log('📦 Using @vercel/static-build strategy');
  console.log(`   Source: ${staticBuild.src}`);
  console.log(`   distDir: ${staticBuild.config?.distDir || 'dist'}`);
  
  // Check for conflicting root rewrites
  if (vercelJson.rewrites) {
    const rootRewrites = vercelJson.rewrites.filter(r => 
      r.source === '/(.*' || r.source === '/(*)' || r.source === '/*' || r.source === '/(.*)' || r.source === '/'
    );
    
    if (rootRewrites.length > 0) {
      rootRewrites.forEach(rw => {
        // Check if rewriting to a source path (not deployed path)
        if (rw.destination.includes('/dist/') || rw.destination.includes(staticBuild.src.replace('/package.json', ''))) {
          console.error(`❌ Conflicting root rewrite detected:`);
          console.error(`   ${rw.source} -> ${rw.destination}`);
          console.error(`   This will cause 404 because @vercel/static-build serves at root`);
          console.error(`   Remove this rewrite or change to serve from root`);
          hasIssues = true;
        }
      });
    }
  }
  
  // Check for redundant framework preset keys
  if (vercelJson.buildCommand) {
    console.warn(`⚠️  'buildCommand' is redundant when using builds array`);
    console.warn(`   The build command comes from ${staticBuild.src}`);
  }
  
  if (vercelJson.outputDirectory) {
    console.warn(`⚠️  'outputDirectory' is redundant when using builds array`);
    console.warn(`   The output directory is specified in builds config`);
  }
  
  // Verify the source file exists
  if (!fs.existsSync(staticBuild.src)) {
    console.error(`❌ Source file not found: ${staticBuild.src}`);
    hasIssues = true;
  } else {
    console.log(`✅ Source file exists: ${staticBuild.src}`);
  }
  
  // Check if build output exists (warning only)
  const uiDir = staticBuild.src.replace('/package.json', '');
  const distDir = staticBuild.config?.distDir || 'dist';
  const distPath = `${uiDir}/${distDir}`;
  const indexPath = `${distPath}/index.html`;
  
  if (fs.existsSync(indexPath)) {
    console.log(`✅ Build output verified: ${indexPath}`);
  } else {
    console.warn(`⚠️  Build output not found: ${indexPath}`);
    console.warn(`   Run 'npm run build' to generate it`);
  }
  
  // Check for SPA fallback configuration
  console.log('\n🔄 Checking SPA fallback configuration...');
  
  if (vercelJson.rewrites) {
    const spaFallback = vercelJson.rewrites.find(r => 
      (r.source === '/(.*' || r.source === '/(*)' || r.source === '/*' || r.source === '/(.*)') && 
      (r.destination === '/index.html' || r.destination === '/')
    );
    
    const apiRewrite = vercelJson.rewrites.find(r => 
      r.source.includes('/api/')
    );
    
    if (!spaFallback) {
      console.error(`❌ Missing SPA fallback rewrite!`);
      console.error(`   Client-side routes will 404 on refresh`);
      console.error(`   Add: {"source": "/(.*)", "destination": "/index.html"}`);
      hasIssues = true;
    } else {
      console.log(`✅ SPA fallback configured: ${spaFallback.source} → ${spaFallback.destination}`);
      
      // Ensure API rewrites come BEFORE SPA fallback
      if (apiRewrite && spaFallback) {
        const apiIndex = vercelJson.rewrites.indexOf(apiRewrite);
        const spaIndex = vercelJson.rewrites.indexOf(spaFallback);
        
        if (apiIndex > spaIndex) {
          console.error(`❌ Rewrite order issue: API rewrite must come BEFORE SPA fallback`);
          console.error(`   Current order will intercept API calls with index.html`);
          hasIssues = true;
        } else {
          console.log(`✅ Rewrite order correct: API routes protected from SPA fallback`);
        }
      }
    }
  } else {
    console.error(`❌ No rewrites array found - SPA routing will not work`);
    hasIssues = true;
  }
}

// Check for legacy routes key
if (vercelJson.routes) {
  console.error(`\n❌ Legacy 'routes' key detected`);
  console.error(`   Use 'rewrites', 'redirects', 'headers' instead`);
  hasIssues = true;
}

console.log('\n' + (hasIssues ? '❌ Routing validation FAILED - Fix issues to prevent 404s' : '✅ Routing validation PASSED'));
process.exit(hasIssues ? 1 : 0);

