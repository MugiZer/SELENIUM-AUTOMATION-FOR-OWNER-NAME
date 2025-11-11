const fs = require('fs');

const files = [
  'vercel.json',
  'package.json',
  'simple_ui/package.json'
];

let allValid = true;

files.forEach(f => {
  try {
    const content = fs.readFileSync(f, 'utf8');
    JSON.parse(content);
    console.log(`✅ ${f} - Valid JSON`);
  } catch (e) {
    console.error(`❌ ${f} - INVALID: ${e.message}`);
    allValid = false;
  }
});

if (!allValid) {
  console.error('\n❌ JSON validation failed');
  process.exit(1);
} else {
  console.log('\n✅ All JSON files are valid');
}

