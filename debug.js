const fs = require('fs');
const vercelJson = JSON.parse(fs.readFileSync('vercel.json', 'utf8'));
console.log('Rewrites array:', vercelJson.rewrites);
vercelJson.rewrites.forEach((r, i) => {
  console.log(`Rewrite ${i}: source='${r.source}', dest='${r.destination}'`);
  const isMatch = (r.source === '/(.*)' || r.source === '/(*)' || r.source === '/*' || r.source === '/(.*)' || r.source === '/');
  console.log(`  Match check: ${isMatch}`);
});
