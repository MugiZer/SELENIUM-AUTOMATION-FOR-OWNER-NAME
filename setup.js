import fs from 'fs';
import readline from 'readline';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
import crypto from 'crypto';

const require = createRequire(import.meta.url);

// Get directory name in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const questions = [
  {
    name: 'MONTREAL_EMAIL',
    message: 'Enter your Montreal email:',
    validate: (input) => !!input || 'Email is required'
  },
  {
    name: 'MONTREAL_PASSWORD',
    message: 'Enter your Montreal password (input will be hidden):',
    hidden: true,
    validate: (input) => !!input || 'Password is required'
  },
  {
    name: 'GOOGLE_SERVICE_ACCOUNT_JSON',
    message: 'Paste your Google Service Account JSON (minified, all in one line):',
    multiline: true,
    validate: (input) => {
      try {
        JSON.parse(input);
        return true;
      } catch (e) {
        return 'Invalid JSON. Please provide a valid JSON string';
      }
    }
  },
  {
    name: 'SHEET_NAME',
    message: 'Enter Google Sheet name (default: Sheet1):',
    default: 'Sheet1'
  },
  {
    name: 'SHEET_TAB',
    message: 'Enter Google Sheet tab name (default: Data):',
    default: 'Data'
  },
  {
    name: 'DELAY_MIN',
    message: 'Minimum delay between requests in seconds (default: 1.5):',
    default: '1.5',
    validate: (input) => {
      const num = parseFloat(input);
      return !isNaN(num) && num > 0 || 'Please enter a valid number greater than 0';
    }
  },
  {
    name: 'DELAY_MAX',
    message: 'Maximum delay between requests in seconds (default: 3.0):',
    default: '3.0',
    validate: (input) => {
      const num = parseFloat(input);
      return !isNaN(num) && num > 0 || 'Please enter a valid number greater than 0';
    }
  }
];

function askQuestion(question) {
  return new Promise(async (resolve) => {
    const options = {
      prompt: `${question.message}${question.default ? ` (${question.default})` : ''}: `
    };

    if (question.hidden) {
      const readline = await import('readline');
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
      });

      const { stdin } = process;
      const listener = (char) => {
        char = char + '';
        switch (char) {
          case '\n':
          case '\r':
          case '\u0004':
            stdin.removeListener('data', listener);
            break;
          default:
            process.stdout.clearLine();
            readline.cursorTo(process.stdout, 0);
            process.stdout.write(options.prompt + Array(rl.line.length + 1).join('*'));
            break;
        }
      };

      process.stdin.on('data', listener);
      rl.question(options.prompt, (value) => {
        rl.history = rl.history.slice(1);
        rl.close();
        resolve(value || question.default || '');
      });
    } else {
      rl.question(options.prompt, (answer) => {
        resolve(answer || question.default || '');
      });
    }
  });
}

async function runSetup() {
  console.log('\n🚀 Setting up your environment...\n');
  
  const answers = {};
  
  for (const question of questions) {
    let answer;
    let isValid = false;
    
    while (!isValid) {
      answer = await askQuestion(question);
      
      if (question.validate) {
        const validation = question.validate(answer);
        if (validation === true) {
          isValid = true;
        } else {
          console.log(`❌ ${validation}`);
          continue;
        }
      } else {
        isValid = true;
      }
      
      if (answer) {
        answers[question.name] = answer;
      }
    }
  }

  // Create .env content
  const envContent = `# Server Configuration
NODE_ENV=development
PORT=3000
SESSION_SECRET=${crypto.randomBytes(32).toString('hex')}

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:3000
FRONTEND_URL=http://localhost:8080

# CORS Configuration
CORS_ORIGIN=http://localhost:8080,http://localhost:5173

# Scraper Configuration
${Object.entries(answers)
  .map(([key, value]) => `${key}=${value}`)
  .join('\n')}
`;

  // Write to .env file
  const envPath = path.join(__dirname, '.env');
  fs.writeFileSync(envPath, envContent);
  
  console.log('\n✅ Environment setup complete!');
  console.log('📁 Created/Updated .env file with your configuration');
  console.log('\nNext steps:');
  console.log('1. Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the .env file');
  console.log('2. Run `npm install` to install dependencies');
  console.log('3. Run `npm run dev` to start the development server\n');
  
  rl.close();
}

runSetup().catch((error) => {
  console.error('❌ Error during setup:', error);
  process.exit(1);
});
