const fs = require('fs');
const path = require('path');

const VERCEL_JSON_PATH = path.join(__dirname, '..', 'vercel.json');
const ROUTES_INDEX_PATH = path.join(__dirname, '..', 'routes', 'index.js');

function validateRouting() {
  console.log('🔍 Validating Vercel routing configuration...\n');

  // Check vercel.json exists and is valid
  if (!fs.existsSync(VERCEL_JSON_PATH)) {
    console.error('❌ ERROR: vercel.json does not exist');
    process.exit(1);
  }

  let vercelConfig;
  try {
    const content = fs.readFileSync(VERCEL_JSON_PATH, 'utf8');
    vercelConfig = JSON.parse(content);
  } catch (error) {
    console.error('❌ ERROR: vercel.json contains invalid JSON');
    console.error(`   ${error.message}`);
    process.exit(1);
  }

  let errors = [];
  let warnings = [];

  // Check for literal ... tokens
  const configString = JSON.stringify(vercelConfig);
  if (configString.includes('...')) {
    errors.push('Found literal "..." token in vercel.json - this indicates incomplete configuration');
  }

  // Check for headers nested inside rewrites
  if (vercelConfig.rewrites) {
    vercelConfig.rewrites.forEach((rewrite, index) => {
      if (rewrite.headers) {
        errors.push(`Rewrite rule ${index} contains nested headers - headers should be at top-level only`);
      }
    });
  }

  // Check for rewrites targeting build-time paths
  const buildPaths = ['/dist', '/simple_ui/dist', '/build', '/server.js'];
  if (vercelConfig.rewrites) {
    vercelConfig.rewrites.forEach((rewrite, index) => {
      buildPaths.forEach(buildPath => {
        if (rewrite.destination && rewrite.destination.includes(buildPath)) {
          errors.push(`Rewrite rule ${index} targets build-time path "${rewrite.destination}" - this will 404 at runtime`);
        }
      });
    });
  }

  // Check for API rewrites targeting static paths
  if (vercelConfig.rewrites) {
    vercelConfig.rewrites.forEach((rewrite, index) => {
      if (rewrite.source && rewrite.source.includes('/api/') && rewrite.destination) {
        if (rewrite.destination.includes('.js') || rewrite.destination.startsWith('/')) {
          warnings.push(`Rewrite rule ${index} routes API to static path "${rewrite.destination}" - consider using Vercel auto-mounting instead`);
        }
      }
    });
  }

  // Check if API build exists and is properly configured
  if (vercelConfig.builds) {
    const apiBuild = vercelConfig.builds.find(build => build.use === '@vercel/node');
    if (!apiBuild) {
      errors.push('No @vercel/node build configuration found for API');
    } else if (!apiBuild.src.startsWith('api/')) {
      warnings.push(`API build source "${apiBuild.src}" doesn't use Vercel auto-mounting pattern (api/*)`);
    }
  }

  // Check routes/index.js for double /api prefixes
  if (fs.existsSync(ROUTES_INDEX_PATH)) {
    try {
      const routesContent = fs.readFileSync(ROUTES_INDEX_PATH, 'utf8');
      const doubleApiMatches = routesContent.match(/router\.use\(['"`]\/api\//g);
      if (doubleApiMatches && doubleApiMatches.length > 0) {
        errors.push(`routes/index.js contains ${doubleApiMatches.length} route(s) with /api/ prefix - this creates /api/api/* paths`);
      }
    } catch (error) {
      warnings.push('Could not read routes/index.js for validation');
    }
  }

  // Report results
  if (errors.length > 0) {
    console.error('❌ Routing validation FAILED:');
    errors.forEach(error => console.error(`   - ${error}`));
    console.error('\n🔧 Fix these issues before deploying to prevent 404 errors.');
    process.exit(1);
  }

  if (warnings.length > 0) {
    console.log('⚠️  Routing validation PASSED with warnings:');
    warnings.forEach(warning => console.log(`   - ${warning}`));
    console.log('');
  }

  console.log('✅ Routing validation PASSED:');
  console.log('   - No literal ... tokens');
  console.log('   - Headers properly at top-level');
  console.log('   - No rewrites target build-time paths');
  console.log('   - API routing uses auto-mounting pattern');
  console.log('   - No double /api prefixes in routes');

  return true;
}

// Run validation
try {
  validateRouting();
  console.log('\n🎉 All routing guardrails passed!');
} catch (error) {
  console.error('\n💥 Unexpected error during validation:', error.message);
  process.exit(1);
}
