const fs = require('fs');
const path = require('path');
const { defineConfig } = require('@playwright/test');

const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split(/\n/).forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return;
    const [key, ...rest] = trimmed.split('=');
    if (!process.env[key]) {
      process.env[key] = rest.join('=').trim();
    }
  });
}

const baseURL = process.env.PLAYWRIGHT_BASE_URL || process.env.REACT_APP_BACKEND_URL;
if (!baseURL) {
  throw new Error('PLAYWRIGHT_BASE_URL veya REACT_APP_BACKEND_URL tanımlanmalı.');
}

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 60000,
  use: {
    baseURL,
    headless: true,
  },
});