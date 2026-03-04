import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

const PROJECT_ROOT = '/app/frontend';
const SRC_ROOT = path.join(PROJECT_ROOT, 'src');
const LEGACY_LOCALES = {
  'src/locales/tr.json': '707e7907f2d57304fb99afca726c83497bf0283d2d532a970cc978a33df7db81',
  'src/locales/de.json': 'ac23428560cc7678e796459463c36029b93d45d03b55cb296d4006d28bcae7f3',
  'src/locales/fr.json': '9c27e1e338819e5af538d7158c312e10f49337d150f84f1d36cefd6d694a8526',
};

const IMPORT_PATTERNS = [
  /locales\/tr\.json/g,
  /locales\/de\.json/g,
  /locales\/fr\.json/g,
];

const hashFile = (absolutePath) => {
  const content = fs.readFileSync(absolutePath);
  return crypto.createHash('sha256').update(content).digest('hex');
};

const collectSourceFiles = (dir) => {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;
    const absolutePath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectSourceFiles(absolutePath));
      continue;
    }

    if (/\.(js|jsx|ts|tsx|mjs|cjs)$/.test(entry.name)) {
      files.push(absolutePath);
    }
  }

  return files;
};

const main = () => {
  const violations = [];

  for (const [relativePath, expectedHash] of Object.entries(LEGACY_LOCALES)) {
    const absolutePath = path.join(PROJECT_ROOT, relativePath);
    if (!fs.existsSync(absolutePath)) {
      violations.push(`[missing] ${relativePath} bulunamadı. Legacy dosyalar migrasyon süresince read-only tutulmalı.`);
      continue;
    }

    const actualHash = hashFile(absolutePath);
    if (actualHash !== expectedHash) {
      violations.push(`[modified] ${relativePath} değiştirildi. Bu dosyalar deprecate/read-only statüsünde.`);
    }
  }

  const sourceFiles = collectSourceFiles(SRC_ROOT);
  for (const filePath of sourceFiles) {
    const content = fs.readFileSync(filePath, 'utf8');
    for (const pattern of IMPORT_PATTERNS) {
      if (pattern.test(content)) {
        const rel = path.relative(PROJECT_ROOT, filePath);
        violations.push(`[import] ${rel} legacy locale dosyasına referans içeriyor.`);
      }
      pattern.lastIndex = 0;
    }
  }

  if (violations.length) {
    console.error('❌ Legacy locale deprecate kuralı ihlali:');
    for (const item of violations) {
      console.error(` - ${item}`);
    }
    process.exit(1);
  }

  console.log('✅ Legacy locale deprecate/read-only kontrolleri geçti.');
};

main();
