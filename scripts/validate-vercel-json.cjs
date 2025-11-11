const fs = require('fs');
const path = require('path');
const VERCEL_JSON_PATH = path.join(__dirname, '..', 'vercel.json');
function validateVercelJson(fix = false) {
  if (!fs.existsSync(VERCEL_JSON_PATH)) {
    console.error(` ERROR: ${VERCEL_JSON_PATH} does not exist`);
    process.exit(1);
  }
  const stats = fs.statSync(VERCEL_JSON_PATH);
  if (stats.size === 0) {
    console.error(` ERROR: ${VERCEL_JSON_PATH} is empty (0 bytes)`);
    console.error('   Root cause: File corruption or incomplete write operation');
    process.exit(2);
  }
  let content, config;
  try {
    content = fs.readFileSync(VERCEL_JSON_PATH, 'utf8');
    if (content.charCodeAt(0) === 0xFEFF) content = content.slice(1);
    config = JSON.parse(content);
  } catch (error) {
    console.error(` ERROR: Invalid JSON syntax`);
    console.error(`   ${error.message}`);
    process.exit(1);
  }
  if ('routes' in config && ('rewrites' in config || 'redirects' in config || 'headers' in config)) {
    console.error(` ERROR: Legacy 'routes' key found alongside modern routing keys`);
    if (fix) {
      delete config.routes;
      fs.writeFileSync(VERCEL_JSON_PATH, JSON.stringify(config, null, 2) + '\n', 'utf8');
      console.log('    Fixed: Removed routes key');
    } else {
      console.error('   Run with --fix to auto-remove');
      process.exit(3);
    }
  }
  console.log('\n Validation passed:');
  console.log(`   - File size: ${stats.size} bytes`);
  console.log(`   - JSON syntax: Valid`);
  console.log(`   - No legacy routes key`);
  return true;
}
const fix = process.argv.includes('--fix');
try {
  validateVercelJson(fix);
  process.exit(0);
} catch (error) {
  console.error('\n Unexpected error:', error.message);
  process.exit(5);
}
