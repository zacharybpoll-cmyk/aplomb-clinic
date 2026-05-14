#!/usr/bin/env node
/**
 * optimize-images.mjs
 * Converts all JPG/PNG images in assets/ to WebP variants (1x and 2x).
 * Idempotent: skips files where WebP is already newer than source.
 */

import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = path.join(__dirname, '..', 'assets');

async function optimizeImages() {
  // Find all JPG/PNG files
  const files = fs.readdirSync(ASSETS_DIR)
    .filter(f => /\.(jpg|jpeg|png)$/i.test(f))
    .map(f => path.join(ASSETS_DIR, f));

  if (files.length === 0) {
    console.log('No images found in assets/');
    return;
  }

  let totalOriginalBytes = 0;
  let totalWebpBytes = 0;
  const results = [];

  console.log(`Found ${files.length} image(s) to process...\n`);

  for (const srcPath of files) {
    const srcStat = fs.statSync(srcPath);
    const srcBytes = srcStat.size;
    totalOriginalBytes += srcBytes;

    const basename = path.basename(srcPath, path.extname(srcPath));
    const webpPath = path.join(ASSETS_DIR, `${basename}.webp`);
    const webp1xPath = path.join(ASSETS_DIR, `${basename}-1x.webp`);

    // Check if both WebP files exist and are newer than source
    const webpExists = fs.existsSync(webpPath) && fs.statSync(webpPath).mtime > srcStat.mtime;
    const webp1xExists = fs.existsSync(webp1xPath) && fs.statSync(webp1xPath).mtime > srcStat.mtime;

    if (webpExists && webp1xExists) {
      const webpBytes = fs.statSync(webpPath).size;
      const webp1xBytes = fs.statSync(webp1xPath).size;
      totalWebpBytes += webpBytes + webp1xBytes;
      results.push({
        file: path.basename(srcPath),
        status: 'skipped',
        original: srcBytes,
        webp2x: webpBytes,
        webp1x: webp1xBytes,
      });
      continue;
    }

    try {
      // Get source metadata
      const image = sharp(srcPath);
      const metadata = await image.metadata();
      const width = metadata.width || 0;
      const height = metadata.height || 0;

      if (width === 0 || height === 0) {
        console.error(`⚠️  Skipping ${path.basename(srcPath)}: no dimensions`);
        continue;
      }

      // Generate full-resolution WebP (2x)
      if (!webpExists) {
        await image
          .webp({ quality: 85 })
          .toFile(webpPath);
      }

      // Generate 1x WebP (50% width)
      if (!webp1xExists) {
        await sharp(srcPath)
          .resize(Math.round(width / 2), Math.round(height / 2), { fit: 'cover', withoutEnlargement: true })
          .webp({ quality: 85 })
          .toFile(webp1xPath);
      }

      const webpBytes = fs.statSync(webpPath).size;
      const webp1xBytes = fs.statSync(webp1xPath).size;
      totalWebpBytes += webpBytes + webp1xBytes;

      const savingsPercent = (100 * (1 - (webpBytes + webp1xBytes) / srcBytes)).toFixed(1);
      console.log(`✓ ${path.basename(srcPath)}`);
      console.log(`  Original:    ${srcBytes} bytes`);
      console.log(`  WebP 2x:     ${webpBytes} bytes`);
      console.log(`  WebP 1x:     ${webp1xBytes} bytes`);
      console.log(`  Savings:     ${savingsPercent}%\n`);

      results.push({
        file: path.basename(srcPath),
        status: 'converted',
        original: srcBytes,
        webp2x: webpBytes,
        webp1x: webp1xBytes,
      });
    } catch (err) {
      console.error(`✗ Failed to process ${path.basename(srcPath)}: ${err.message}`);
    }
  }

  // Summary
  console.log('='.repeat(60));
  console.log('SUMMARY');
  console.log('='.repeat(60));
  console.log(`Files processed: ${results.filter(r => r.status === 'converted').length} converted, ${results.filter(r => r.status === 'skipped').length} skipped`);
  console.log(`Original total:  ${totalOriginalBytes} bytes (${(totalOriginalBytes / 1048576).toFixed(1)}MB)`);
  console.log(`WebP total:      ${totalWebpBytes} bytes (${(totalWebpBytes / 1048576).toFixed(1)}MB)`);
  const overallSavings = (100 * (1 - totalWebpBytes / totalOriginalBytes)).toFixed(1);
  console.log(`Overall savings: ${overallSavings}%`);
  console.log('='.repeat(60));
}

optimizeImages().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
