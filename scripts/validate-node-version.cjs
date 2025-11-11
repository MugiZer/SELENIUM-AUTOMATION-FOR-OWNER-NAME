const fs = require('fs');

console.log('🔍 Validating Node runtime configuration...\n');

const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
let hasIssues = false;

if (!packageJson.engines || !packageJson.engines.node) {
  console.error('❌ Missing engines.node field in package.json');
  hasIssues = true;
  process.exit(1);
}

const nodeVersion = packageJson.engines.node;
console.log(`Current engines.node: "${nodeVersion}"`);

// Check for floating major versions
const floatingPatterns = [
  /^>=\s*\d+/,  // >= syntax
  /^\^/,        // caret
  /^~/,         // tilde on major
  /^\*/,        // wildcard
  /^latest$/    // latest keyword
];

const isFloating = floatingPatterns.some(pattern => pattern.test(nodeVersion));

if (isFloating) {
  console.error('❌ FAIL: Floating Node version detected!');
  console.error('   This can cause auto-upgrades on Vercel to incompatible majors.');
  console.error('   Use a pinned format like "18.x" or "20.x"');
  hasIssues = true;
} else {
  console.log('✅ Node version is pinned (no floating >= or ^ on major)');
}

// Check if it's a supported LTS
const ltsVersions = ['18.x', '20.x', '22.x'];
if (ltsVersions.includes(nodeVersion)) {
  console.log(`✅ Using supported LTS version: ${nodeVersion}`);
} else if (/^\d+\.x$/.test(nodeVersion)) {
  console.warn(`⚠️  Version ${nodeVersion} may not be LTS. Supported: ${ltsVersions.join(', ')}`);
} else {
  console.log(`ℹ️  Specific version: ${nodeVersion}`);
}

// Document local vs deploy version
console.log('\n📋 Environment Info:');
console.log(`   Local Node: ${process.version}`);
console.log(`   Vercel will use: ${nodeVersion}`);
if (process.version !== nodeVersion && !process.version.startsWith(`v${nodeVersion.split('.')[0]}.`)) {
  console.log('   ⚠️  Local version differs from deployment version');
  console.log('   💡 Consider using nvm/volta to match locally');
}

console.log('\n' + (hasIssues ? '❌ Node validation FAILED' : '✅ Node validation PASSED'));
process.exit(hasIssues ? 1 : 0);

