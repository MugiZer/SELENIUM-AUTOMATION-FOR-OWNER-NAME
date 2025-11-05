import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Configure dotenv
dotenv.config();

const requiredEnvVars = [
  'NODE_ENV',
  'PORT',
  'SESSION_SECRET',
  'GOOGLE_CLIENT_ID',
  'GOOGLE_CLIENT_SECRET',
  'VITE_API_BASE_URL'
];

function validateEnv() {
  const missing = requiredEnvVars.filter(envVar => !process.env[envVar]);
  
  if (missing.length > 0) {
    console.error('❌ Missing required environment variables:');
    missing.forEach(envVar => console.error(`- ${envVar}`));
    console.error('\nPlease run: npm run setup');
    process.exit(1);
  }

  console.log('✅ Environment variables validated');
  return true;
}

export { validateEnv };
