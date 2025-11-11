#!/usr/bin/env node
/**
 * Pre-commit hook to prevent configuration regressions
 * Runs lightweight checks on staged files
 */

const { execSync } = require('child_process');
const fs = require('fs');

console.log('🔍 Running pre-commit validation...\n');

// Check if critical files are staged
const staged = execSync('git diff --cached --name-only', { encoding: 'utf8' }).trim().split('\n');
const criticalFiles = ['vercel.json', 'package.json', 'simple_ui/package.json'];
const stagedCritical = staged.filter(f => criticalFiles.includes(f));

if (stagedCritical.length === 0) {
  console.log('ℹ️  No critical config files changed, skipping validation');
  process.exit(0);
}

console.log(`📝 Critical files staged: ${stagedCritical.join(', ')}\n`);

// Run validations
let failed = false;

try {
  // Always check JSON validity
  execSync('node scripts/validate-json.cjs', { stdio: 'inherit' });
  
  if (stagedCritical.includes('vercel.json')) {
    execSync('node scripts/validate-vercel-schema.cjs', { stdio: 'inherit' });
  }
  
  if (stagedCritical.includes('package.json')) {
    execSync('node scripts/validate-node-version.cjs', { stdio: 'inherit' });
    execSync('node scripts/validate-vercel-packages.cjs', { stdio: 'inherit' });
  }
} catch (error) {
  failed = true;
}

if (failed) {
  console.log('\n❌ Pre-commit validation failed. Fix issues before committing.');
  process.exit(1);
} else {
  console.log('\n✅ Pre-commit validation passed');
  process.exit(0);
}

