#!/usr/bin/env npx tsx
/**
 * Phase 3 MCP Tools Validation Test
 * Tests memory_recall_context, memory_suggestions, and memory_analytics tools
 */

import { recallContext } from '../../src/tools/memory_recall_context.js';
import { getSuggestions } from '../../src/tools/memory_suggestions.js';
import { getAnalytics } from '../../src/tools/memory_analytics.js';

async function testPhase3Tools() {
  console.log('🔍 Testing Phase 3 MCP Tools...\n');

  let passed = 0;
  let failed = 0;

  // ========================================================================
  // Test 1: memory_recall_context
  // ========================================================================
  console.log('Test 1: memory_recall_context Tool');
  console.log('='.repeat(60));

  try {
    console.log('\n1.1 Basic context recall');
    const result1 = await recallContext({
      recent_minutes: 30,
      limit: 10,
    });

    console.log(`  Context active: ${result1.context?.active ?? 'N/A'}`);
    console.log(`  Context type: ${result1.context?.context_type ?? 'N/A'}`);
    console.log(`  Recalled memories: ${result1.recalled_memories?.length ?? 0}`);
    console.log('  ✓ Context recall executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Context recall failed: ${error}`);
    failed++;
  }

  try {
    console.log('\n1.2 With project filter');
    const result2 = await recallContext({
      recent_minutes: 60,
      limit: 5,
      project: 'test-project',
    });

    console.log(`  Result received: ${result2 ? 'Yes' : 'No'}`);
    console.log('  ✓ Filtered recall executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Filtered recall failed: ${error}`);
    failed++;
  }

  // ========================================================================
  // Test 2: memory_suggestions
  // ========================================================================
  console.log('\n\nTest 2: memory_suggestions Tool');
  console.log('='.repeat(60));

  try {
    console.log('\n2.1 Generate suggestions');
    const result1 = await getSuggestions({
      limit: 5,
    });

    console.log(`  Suggestions: ${result1.suggestions?.length ?? 0}`);
    console.log(`  Issues: ${result1.potential_issues?.length ?? 0}`);
    console.log(`  Forgotten: ${result1.forgotten_knowledge?.length ?? 0}`);
    console.log('  ✓ Suggestions generated');
    passed++;
  } catch (error) {
    console.log(`  ✗ Suggestions failed: ${error}`);
    failed++;
  }

  try {
    console.log('\n2.2 With project filter');
    const result2 = await getSuggestions({
      limit: 10,
      project: 'test-project',
    });

    console.log(`  Result received: ${result2 ? 'Yes' : 'No'}`);
    console.log('  ✓ Filtered suggestions executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Filtered suggestions failed: ${error}`);
    failed++;
  }

  // ========================================================================
  // Test 3: memory_analytics
  // ========================================================================
  console.log('\n\nTest 3: memory_analytics Tool');
  console.log('='.repeat(60));

  try {
    console.log('\n3.1 Statistics analytics');
    const result1 = await getAnalytics({
      query_type: 'statistics',
      limit: 10,
      days: 30,
    });

    console.log(`  Query type: ${result1.query_type}`);
    console.log(`  Data received: ${result1.data ? 'Yes' : 'No'}`);
    console.log('  ✓ Statistics analytics executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Statistics analytics failed: ${error}`);
    failed++;
  }

  try {
    console.log('\n3.2 Pattern analytics');
    const result2 = await getAnalytics({
      query_type: 'patterns',
      limit: 10,
      days: 30,
    });

    console.log(`  Query type: ${result2.query_type}`);
    if (result2.data) {
      const patterns = result2.data.patterns || [];
      console.log(`  Patterns found: ${patterns.length}`);
    }
    console.log('  ✓ Pattern analytics executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Pattern analytics failed: ${error}`);
    failed++;
  }

  try {
    console.log('\n3.3 Graph analytics');
    const result3 = await getAnalytics({
      query_type: 'graph',
      limit: 10,
      days: 30,
    });

    console.log(`  Query type: ${result3.query_type}`);
    console.log('  ✓ Graph analytics executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Graph analytics failed: ${error}`);
    failed++;
  }

  try {
    console.log('\n3.4 Trends analytics');
    const result4 = await getAnalytics({
      query_type: 'trends',
      limit: 10,
      days: 30,
    });

    console.log(`  Query type: ${result4.query_type}`);
    if (result4.data) {
      console.log(`  Trend direction: ${result4.data.trend_direction || 'N/A'}`);
    }
    console.log('  ✓ Trends analytics executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Trends analytics failed: ${error}`);
    failed++;
  }

  try {
    console.log('\n3.5 Entity analytics');
    const result5 = await getAnalytics({
      query_type: 'entities',
      limit: 10,
      days: 30,
    });

    console.log(`  Query type: ${result5.query_type}`);
    console.log('  ✓ Entity analytics executed');
    passed++;
  } catch (error) {
    console.log(`  ✗ Entity analytics failed: ${error}`);
    failed++;
  }

  // ========================================================================
  // Summary
  // ========================================================================
  console.log('\n' + '='.repeat(60));
  console.log('PHASE 3 TOOLS VALIDATION SUMMARY');
  console.log('='.repeat(60));
  console.log(`✓ Passed: ${passed}`);
  console.log(`✗ Failed: ${failed}`);
  console.log(`Total: ${passed + failed}`);

  if (failed === 0) {
    console.log('\n✅ All Phase 3 MCP tools validated successfully!');
    process.exit(0);
  } else {
    console.log(`\n⚠ ${failed} test(s) failed`);
    process.exit(1);
  }
}

testPhase3Tools().catch((error) => {
  console.error('Test execution failed:', error);
  process.exit(1);
});
