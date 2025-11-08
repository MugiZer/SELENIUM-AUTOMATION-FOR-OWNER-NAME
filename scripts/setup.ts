import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { createInterface } from 'readline';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { randomBytes } from 'crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface EnvConfig {
  // Google OAuth
  GOOGLE_CLIENT_ID: string;
  GOOGLE_CLIENT_SECRET: string;
  SESSION_SECRET: string;
  NODE_ENV: 'development' | 'production';
  PORT: string;
  FRONTEND_URL: string;
  VITE_API_BASE_URL: string;
  
  // Scraper Config
  MONTREAL_EMAIL: string;
  MONTREAL_PASSWORD: string;
  GOOGLE_SERVICE_ACCOUNT_JSON: string;
  SHEET_NAME: string;
  SHEET_TAB: string;
  DELAY_MIN: string;
  DELAY_MAX: string;
  CACHE_PATH: string;
  LOG_LEVEL: string;
}

const rl = createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = (query: string, defaultValue: string = ''): Promise<string> => {
  return new Promise((resolve) => {
    const prompt = defaultValue ? `${query} [${defaultValue}]: ` : `${query}: `;
    rl.question(prompt, (answer) => {
      resolve(answer || defaultValue);
    });
  });
};

const generateSessionSecret = (): string => {
  return randomBytes(32).toString('hex');
};

const setup = async () => {
  console.clear();
  console.log('🚀 Welcome to the Montreal Property Scraper Setup 🚀');
  console.log('Please provide the following configuration values (press Enter to use defaults):\n');

  let existingConfig: Partial<EnvConfig> = {};
  const envPath = join(process.cwd(), '.env');

  // Load existing config if it exists
  if (existsSync(envPath)) {
    console.log('📝 Found existing .env file. Current values will be used as defaults.\n');
    const envContent = readFileSync(envPath, 'utf-8');
    envContent.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split('=');
      const trimmedKey = key.trim() as keyof EnvConfig;
      const value = valueParts.join('=').trim();
      
      if (trimmedKey && !trimmedKey.startsWith('#')) {
        // Special handling for NODE_ENV to ensure it's either 'development' or 'production'
        if (trimmedKey === 'NODE_ENV' && value) {
          existingConfig[trimmedKey] = (value === 'production' ? 'production' : 'development') as any;
        } else {
          (existingConfig[trimmedKey] as any) = value;
        }
      }
    });
  }

  // Google OAuth Section
  console.log('\n🔐 Google OAuth Configuration');
  console.log('----------------------------');
  const googleClientId = await question(
    'Google OAuth Client ID',
    existingConfig.GOOGLE_CLIENT_ID || '577270563274-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com'
  );

  const googleClientSecret = await question(
    'Google OAuth Client Secret',
    existingConfig.GOOGLE_CLIENT_SECRET || 'GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
  );

  // Scraper Configuration Section
  console.log('\n🛠️  Scraper Configuration');
  console.log('----------------------');
  const montrealEmail = await question(
    'Montreal Service Email',
    existingConfig.MONTREAL_EMAIL || ''
  );

  const montrealPassword = await question(
    'Montreal Service Password',
    existingConfig.MONTREAL_PASSWORD || ''
  );

  const sheetName = await question(
    'Google Sheet Name',
    existingConfig.SHEET_NAME || 'Property Data'
  );

  const sheetTab = await question(
    'Google Sheet Tab Name',
    existingConfig.SHEET_TAB || 'Sheet1'
  );

  // Generate default values for missing required fields
  const sessionSecret = existingConfig.SESSION_SECRET || generateSessionSecret();
  const nodeEnv = existingConfig.NODE_ENV || 'development';
  const port = existingConfig.PORT || '3000';
  const frontendUrl = existingConfig.FRONTEND_URL || 'http://localhost:5173';
  const apiBaseUrl = existingConfig.VITE_API_BASE_URL || 'http://localhost:3000';
  const delayMin = existingConfig.DELAY_MIN || '1.5';
  const delayMax = existingConfig.DELAY_MAX || '3.0';
  const cachePath = existingConfig.CACHE_PATH || 'cache.sqlite';
  const logLevel = existingConfig.LOG_LEVEL || 'INFO';

  // Generate .env content
  const envContent = `# Google OAuth for Web UI
GOOGLE_CLIENT_ID=${googleClientId}
GOOGLE_CLIENT_SECRET=${googleClientSecret}
SESSION_SECRET=${sessionSecret}
NODE_ENV=${nodeEnv}
PORT=${port}
FRONTEND_URL=${frontendUrl}
VITE_API_BASE_URL=${apiBaseUrl}

# Montreal role scraper configuration
MONTREAL_EMAIL=${montrealEmail}
MONTREAL_PASSWORD=${montrealPassword}
GOOGLE_SERVICE_ACCOUNT_JSON=${existingConfig.GOOGLE_SERVICE_ACCOUNT_JSON || ''}
SHEET_NAME=${sheetName}
SHEET_TAB=${sheetTab}
DELAY_MIN=${delayMin}
DELAY_MAX=${delayMax}
CACHE_PATH=${cachePath}
LOG_LEVEL=${logLevel}
`;

  // Ensure scripts directory exists
  if (!existsSync(join(process.cwd(), 'scripts'))) {
    mkdirSync(join(process.cwd(), 'scripts'), { recursive: true });
  }

  // Write to .env file
  writeFileSync(envPath, envContent);
  console.log('\n✅ Configuration saved to .env file');
  
  // Add setup script to package.json if it doesn't exist
  const packageJsonPath = join(process.cwd(), 'package.json');
  if (existsSync(packageJsonPath)) {
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));
    if (!packageJson.scripts) {
      packageJson.scripts = {};
    }
    
    if (!packageJson.scripts.setup) {
      packageJson.scripts.setup = "ts-node scripts/setup.ts";
      writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
      console.log('\n🔧 Added "setup" script to package.json');
    }
  }

  console.log('\n🚀 Setup complete! You can now start the application with:');
  console.log('1. Install dependencies: npm install');
  console.log('2. Run the application: npm run dev\n');

  rl.close();};

setup().catch(err => {
  console.error('\n❌ An error occurred during setup:');
  console.error(err);
  process.exit(1);
});
