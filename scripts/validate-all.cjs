#!/usr/bin/env node
/**
 * Master validation script - runs all Vercel deployment checks
 * This prevents configuration regressions that cause deployment failures
 */

const { execSync } = require('child_process');
const fs = require('fs');

const checks = [
  {
    name: 'JSON Validity',
    script: 'node scripts/validate-json.cjs',
    critical: true
  },
  {
    name: 'Vercel Schema',
    script: 'node scripts/validate-vercel-schema.cjs',
    critical: true
  },
  {
    name: 'Node Version',
    script: 'node scripts/validate-node-version.cjs',
    critical: true
  },
  {
    name: 'Vercel Packages',
    script: 'node scripts/validate-vercel-packages.cjs',
    critical: true
  },
  {
    name: 'Build Config',
    script: 'node scripts/validate-build-config.cjs',
    critical: true
  }
];

console.log('🚀 Running Vercel Deployment Validation Suite\n');
console.log('='.repeat(60));

let failures = 0;
let warnings = 0;

checks.forEach((check, idx) => {
  console.log(`\n[${idx + 1}/${checks.length}] ${check.name}...`);
  console.log('-'.repeat(60));
  
  try {
    execSync(check.script, { 
      stdio: 'inherit',
      cwd: process.cwd()
    });
  } catch (error) {
    if (check.critical) {
      failures++;
      console.error(`\n❌ CRITICAL FAILURE: ${check.name}`);
    } else {
      warnings++;
      console.warn(`\n⚠️  WARNING: ${check.name}`);
    }
  }
});

console.log('\n' + '='.repeat(60));
console.log('\n📊 Validation Summary:');
console.log(`   ✅ Passed: ${checks.length - failures - warnings}`);
if (warnings > 0) console.log(`   ⚠️  Warnings: ${warnings}`);
if (failures > 0) console.log(`   ❌ Failures: ${failures}`);

if (failures > 0) {
  console.log('\n❌ VALIDATION FAILED - Fix critical issues before deploying');
  process.exit(1);
} else if (warnings > 0) {
  console.log('\n⚠️  VALIDATION PASSED WITH WARNINGS - Review before deploying');
  process.exit(0);
} else {
  console.log('\n✅ ALL VALIDATIONS PASSED - Ready for deployment');
  process.exit(0);
}

