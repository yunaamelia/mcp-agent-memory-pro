#!/usr/bin/env node

/**
 * Format validation report for GitHub Actions output
 */

const fs = require('fs');

const REPORT_PATH = process.argv[2] || 'poc/validation-report.json';

try {
  const report = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));

  console.log('## Phase 0 Validation Report\n');

  const statusEmoji = report.status === 'passed' ? '✅' : '❌';
  console.log(`**Status**: ${statusEmoji} ${report.status.toUpperCase()}\n`);

  console.log('### Summary\n');
  console.log('| Metric | Value |');
  console.log('|--------|-------|');
  console.log(`| Total Tests | ${report.summary.total} |`);
  console.log(`| Passed | ${report.summary.passed} |`);
  console.log(`| Failed | ${report.summary.failed} |`);
  console.log(`| Duration | ${report.duration_seconds}s |\n`);

  console.log('### Test Results\n');
  for (const test of report.tests) {
    const emoji = test.status === 'passed' ? '✅' : test.status === 'failed' ? '❌' : '⏭️';
    console.log(`${emoji} **${test.name}** (${test.duration_seconds}s)`);
    if (test.details) {
      console.log(`   ${test.details}`);
    }
  }

  process.exit(report.status === 'passed' ? 0 : 1);
} catch (error) {
  console.error('❌ Error reading validation report:', error.message);
  process.exit(1);
}
