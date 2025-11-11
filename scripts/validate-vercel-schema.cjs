const fs = require('fs');

// Validate vercel.json schema compliance
const vercelJson = JSON.parse(fs.readFileSync('vercel.json', 'utf8'));

console.log('🔍 Validating vercel.json schema...\n');

let hasIssues = false;

// Check version
if (!vercelJson.version || vercelJson.version !== 2) {
  console.error('❌ Missing or incorrect "version" field (should be 2)');
  hasIssues = true;
} else {
  console.log('✅ Version: 2 (modern schema)');
}

// Check for legacy keys
const legacyKeys = ['routes'];
const foundLegacy = legacyKeys.filter(key => key in vercelJson);
if (foundLegacy.length > 0) {
  console.error(`❌ Legacy keys found: ${foundLegacy.join(', ')}`);
  hasIssues = true;
} else {
  console.log('✅ No legacy routing keys (routes) detected');
}

// Check for modern routing keys
const modernKeys = ['rewrites', 'redirects', 'headers', 'cleanUrls', 'trailingSlash'];
const foundModern = modernKeys.filter(key => key in vercelJson);
if (foundModern.length > 0) {
  console.log(`✅ Modern routing keys found: ${foundModern.join(', ')}`);
}

// Validate builds array
if (vercelJson.builds && Array.isArray(vercelJson.builds)) {
  console.log(`✅ Builds array valid (${vercelJson.builds.length} build(s))`);
  vercelJson.builds.forEach((build, idx) => {
    if (!build.src || !build.use) {
      console.error(`❌ Build ${idx}: missing src or use field`);
      hasIssues = true;
    } else {
      console.log(`   - Build ${idx}: ${build.src} -> ${build.use}`);
    }
  });
}

// Check for proper JSON formatting
const content = fs.readFileSync('vercel.json', 'utf8');
if (content.includes('//') || content.includes('/*')) {
  console.error('❌ Comments detected in JSON (not allowed)');
  hasIssues = true;
} else {
  console.log('✅ No comments in JSON');
}

if (!content.endsWith('\n')) {
  console.warn('⚠️  Missing newline at end of file');
}

console.log('\n' + (hasIssues ? '❌ Schema validation FAILED' : '✅ Schema validation PASSED'));
process.exit(hasIssues ? 1 : 0);

