const fs = require('fs');
const https = require('https');
const { promisify } = require('util');

console.log('🔍 Validating @vercel/* package versions...\n');

const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const allDeps = {
  ...packageJson.dependencies,
  ...packageJson.devDependencies
};

const vercelPackages = Object.entries(allDeps).filter(([name]) => name.includes('vercel'));

if (vercelPackages.length === 0) {
  console.log('ℹ️  No @vercel/* packages found');
  process.exit(0);
}

console.log('Found Vercel packages:');
vercelPackages.forEach(([name, version]) => {
  console.log(`  ${name}: ${version}`);
});
console.log();

let hasIssues = false;

// Check for problematic version patterns
vercelPackages.forEach(([name, version]) => {
  // Check for beta/next/canary
  if (/beta|next|canary|alpha|rc/.test(version)) {
    console.error(`❌ ${name}: Unstable version detected (${version})`);
    console.error(`   Recommendation: Use stable version without pre-release tags`);
    hasIssues = true;
  }
  
  // Check for major version 4+ on @vercel/node (ETARGET issues)
  if (name === '@vercel/node' && /[\^~]?4/.test(version)) {
    console.error(`❌ ${name}: Version 4.x may not exist or be unstable`);
    console.error(`   Recommendation: Use ^3.x (latest stable major)`);
    hasIssues = true;
  }
  
  // Check for loose ranges
  if (version.includes('||') || version.includes('*') || version.startsWith('>=')) {
    console.warn(`⚠️  ${name}: Very loose version range (${version})`);
    console.warn(`   Consider using caret (^) or tilde (~) for stability`);
  }
});

if (!hasIssues) {
  console.log('✅ All @vercel/* package versions are stable');
  console.log('✅ No major version 4+ @vercel/node detected');
  console.log('✅ No beta/next/canary versions detected');
}

// Check lockfile exists
if (!fs.existsSync('package-lock.json')) {
  console.warn('\n⚠️  No package-lock.json found - dependencies may drift');
} else {
  console.log('\n✅ package-lock.json present (dependency pinning)');
}

// Check for competing lockfiles
const lockfiles = ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'];
const presentLockfiles = lockfiles.filter(f => fs.existsSync(f));
if (presentLockfiles.length > 1) {
  console.error(`\n❌ Multiple lockfiles detected: ${presentLockfiles.join(', ')}`);
  console.error('   Keep only one to avoid package manager conflicts');
  hasIssues = true;
} else if (presentLockfiles.length === 1) {
  console.log(`✅ Single package manager: ${presentLockfiles[0].replace('-lock', '').replace('.yaml', '')}`);
}

console.log('\n' + (hasIssues ? '❌ Package validation FAILED' : '✅ Package validation PASSED'));
process.exit(hasIssues ? 1 : 0);

