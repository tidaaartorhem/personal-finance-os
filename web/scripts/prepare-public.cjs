/**
 * Build step: regenerate finance.json from the deterministic Python pipeline.
 *
 * The pipeline (services/main.py) reads data/sample-transactions.csv and
 * writes web/public/finance.json. This script runs it before every vite
 * build so the dashboard always ships freshly computed data.
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const webDir = path.resolve(__dirname, '..');
const target = path.resolve(webDir, 'public', 'finance.json');

try {
  execSync('python3 ../services/main.py build', {
    cwd: webDir,
    stdio: 'inherit',
  });
} catch (err) {
  console.error('prepare-public: pipeline failed');
  process.exit(1);
}

if (!fs.existsSync(target)) {
  console.error('prepare-public: finance.json was not produced');
  process.exit(1);
}
console.log('prepare-public: finance.json ready');
